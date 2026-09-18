#!/usr/bin/env python
"""
Executable smoke check for DATA-API.yaml.

Run it against a started UniPath MAX stack. The script intentionally uses only
the public HTTP API and verifies the subscription -> notification flow after an
admin publishes a matching opportunity.
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Any

import requests


STUDENT = {"email": "student@demo.local", "password": "demo12345"}
ADMIN = {"email": "admin@demo.local", "password": "demo12345"}


class SmokeFailure(AssertionError):
    pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Run UniPath MAX DATA-API smoke checks.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--timeout", type=float, default=10.0, help="Request timeout in seconds")
    args = parser.parse_args()

    smoke = Smoke(base_url=args.base_url.rstrip("/"), timeout=args.timeout)
    try:
        smoke.run()
    except SmokeFailure as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(f"FAIL: HTTP request failed: {exc}", file=sys.stderr)
        return 1

    print("PASS: DATA-API smoke scenario completed, including simulated notification dedupe.")
    return 0


class Smoke:
    def __init__(self, base_url: str, timeout: float) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.student_token = ""
        self.admin_token = ""
        self.topic = f"SmokeTopic{int(time.time())}"
        self.opportunity_id = ""

    def run(self) -> None:
        self.health()
        self.student_token = self.login(STUDENT, "student")
        self.prevent_privilege_escalation()
        self.onboarding()
        self.career_gps()
        self.opportunities()
        self.create_subscription()
        self.admin_token = self.login(ADMIN, "admin")
        self.publish_matching_opportunity()
        self.verify_notification(expected_count=1)
        self.republish_without_duplicate()
        self.verify_notification(expected_count=1)
        self.knowledge_search()
        self.admin_analytics()

    def health(self) -> None:
        response = self.request("GET", "/api/health/")
        self.expect(response, 200, "health")
        if response.json().get("status") != "ok":
            raise SmokeFailure("health did not return status=ok")

    def login(self, credentials: dict[str, str], role: str) -> str:
        response = self.request("POST", "/api/auth/login/", json=credentials)
        self.expect(response, 200, f"login_{role}")
        data = response.json()
        if data.get("user", {}).get("role") != role:
            raise SmokeFailure(f"login_{role} returned wrong role: {data.get('user')}")
        token = data.get("access")
        if not token:
            raise SmokeFailure(f"login_{role} did not return access token")
        return token

    def prevent_privilege_escalation(self) -> None:
        response = self.request(
            "POST",
            "/api/auth/register/",
            json={
                "email": f"admin-attempt-{self.topic.lower()}@example.local",
                "password": "demo12345",
                "password2": "demo12345",
                "first_name": "Admin",
                "last_name": "Attempt",
                "role": "admin",
            },
        )
        self.expect(response, 400, "prevent_privilege_escalation")

    def onboarding(self) -> None:
        response = self.request(
            "POST",
            "/api/onboarding",
            token=self.student_token,
            json={
                "universityId": "1",
                "instituteId": "cs",
                "courseId": "1",
                "studyYear": "3",
                "interests": ["Backend", "internships", self.topic],
                "skills": [
                    {"name": "Python", "level": 4},
                    {"name": "Django", "level": 3},
                    {"name": "REST", "level": 3},
                ],
                "careerGoal": "Backend Developer",
            },
        )
        self.expect(response, 200, "onboarding")
        if response.json().get("completed") is not True:
            raise SmokeFailure("onboarding did not complete")

    def career_gps(self) -> None:
        response = self.request("GET", "/api/student/career-gps", token=self.student_token)
        self.expect(response, 200, "career_gps")
        data = response.json()
        if not (0 <= data.get("currentScore", -1) <= data.get("maxScore", 100)):
            raise SmokeFailure("career_gps returned invalid score")
        if not data.get("nextSteps"):
            raise SmokeFailure("career_gps did not return next actions")

    def opportunities(self) -> None:
        response = self.request("GET", "/api/student/opportunities", token=self.student_token)
        self.expect(response, 200, "opportunities")
        items = response.json()
        if not items:
            raise SmokeFailure("opportunities returned no items")
        first = items[0]
        if "matchPercentage" not in first or "matchReasons" not in first or "gaps" not in first:
            raise SmokeFailure("opportunity response does not expose explainable match")
        saved = self.request(
            "POST",
            f"/api/student/opportunities/{first['id']}/save",
            token=self.student_token,
        )
        self.expect(saved, 200, "save_opportunity")

    def create_subscription(self) -> None:
        response = self.request(
            "POST",
            "/api/student/subscriptions",
            token=self.student_token,
            json={"topic": self.topic, "filters": {"topic": self.topic}, "active": True},
        )
        self.expect(response, 201, "create_subscription")
        if response.json().get("topic") != self.topic:
            raise SmokeFailure("subscription topic was not persisted")

    def publish_matching_opportunity(self) -> None:
        response = self.request(
            "POST",
            "/api/admin/opportunities",
            token=self.admin_token,
            json=self.opportunity_payload(),
        )
        self.expect(response, 201, "admin_publish_matching_opportunity")
        self.opportunity_id = str(response.json().get("id") or "")
        if not self.opportunity_id:
            raise SmokeFailure("admin publish did not return opportunity id")

    def republish_without_duplicate(self) -> None:
        response = self.request(
            "PUT",
            f"/api/admin/opportunities/{self.opportunity_id}",
            token=self.admin_token,
            json=self.opportunity_payload(),
        )
        self.expect(response, 200, "admin_republish_matching_opportunity")

    def verify_notification(self, expected_count: int) -> None:
        response = self.request(
            "GET",
            f"/api/v1/notifications/?opportunity={self.opportunity_id}",
            token=self.student_token,
        )
        self.expect(response, 200, "verify_subscription_notification")
        items = self.list_payload(response.json())
        matching = [item for item in items if str(item.get("opportunity_title", "")).endswith(self.topic)]
        if len(matching) != expected_count:
            raise SmokeFailure(
                f"expected {expected_count} notification for opportunity {self.opportunity_id}, got {len(matching)}"
            )
        statuses = {item.get("delivery_status") for item in matching}
        if statuses != {"simulated"}:
            raise SmokeFailure(f"expected delivery_status=simulated, got {sorted(statuses)}")

    def knowledge_search(self) -> None:
        response = self.request(
            "GET",
            "/api/knowledge/search",
            token=self.student_token,
            params={"q": "практика"},
        )
        self.expect(response, 200, "knowledge_search")
        data = response.json()
        if data.get("found") and not data.get("results", [{}])[0].get("source"):
            raise SmokeFailure("knowledge result is missing source")

        fallback = self.request(
            "GET",
            "/api/knowledge/search",
            token=self.student_token,
            params={"q": f"no-answer-{self.topic}"},
        )
        self.expect(fallback, 200, "knowledge_fallback")
        if fallback.json().get("found") is not False:
            raise SmokeFailure("knowledge fallback did not return found=false")
        if not fallback.json().get("escalation"):
            raise SmokeFailure("knowledge fallback is missing escalation")

    def admin_analytics(self) -> None:
        response = self.request("GET", "/api/admin/analytics", token=self.admin_token)
        self.expect(response, 200, "admin_analytics")
        if "totalUsers" not in response.json():
            raise SmokeFailure("admin analytics response is missing totalUsers")

    def opportunity_payload(self) -> dict[str, Any]:
        return {
            "title": f"MAX Smoke Internship {self.topic}",
            "company": "MAX Labs",
            "description": f"Build student notification integrations for {self.topic}.",
            "type": "internship",
            "location": "Campus / Hybrid",
            "remote": True,
            "requirements": ["Python", "Django", "REST", self.topic],
            "status": "active",
        }

    def request(self, method: str, path: str, token: str = "", **kwargs: Any) -> requests.Response:
        headers = kwargs.pop("headers", {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return requests.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            timeout=self.timeout,
            **kwargs,
        )

    def expect(self, response: requests.Response, status_code: int, check_id: str) -> None:
        if response.status_code != status_code:
            raise SmokeFailure(
                f"{check_id} expected HTTP {status_code}, got {response.status_code}: {response.text[:500]}"
            )

    def list_payload(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):
            return payload["results"]
        raise SmokeFailure(f"expected list or paginated list payload, got {payload!r}")


if __name__ == "__main__":
    raise SystemExit(main())
