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
        self.subscription_id = ""
        self.university_id = ""
        self.institute_id = ""
        self.program_id = ""

    def run(self) -> None:
        self.health()
        self.student_token = self.login(STUDENT, "student")
        self.prevent_privilege_escalation()
        self.pick_onboarding_options()
        self.onboarding()
        self.career_gps()
        self.opportunities()
        self.create_subscription()
        self.admin_token = self.login(ADMIN, "admin")
        self.publish_matching_opportunity()
        self.verify_notification(expected_count=1)
        self.open_published_opportunity()
        self.republish_without_duplicate()
        self.verify_notification(expected_count=1)
        self.knowledge_search()
        self.admin_analytics()
        self.cleanup_test_data()

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

    def pick_onboarding_options(self) -> None:
        universities = self.request("GET", "/api/universities", token=self.student_token)
        self.expect(universities, 200, "universities")
        university_items = universities.json()
        university = next((item for item in university_items if item.get("name") == "НИУ МГСУ"), None)
        university = university or (university_items[0] if university_items else None)
        if not university:
            raise SmokeFailure("universities returned no items")
        self.university_id = str(university["id"])

        institutes = self.request(
            "GET",
            "/api/institutes",
            token=self.student_token,
            params={"universityId": self.university_id},
        )
        self.expect(institutes, 200, "institutes")
        institute_items = institutes.json()
        institute = next((item for item in institute_items if "цифров" in item.get("name", "").lower()), None)
        institute = institute or (institute_items[0] if institute_items else None)
        if not institute:
            raise SmokeFailure("institutes returned no items")
        self.institute_id = str(institute["id"])

        programs = self.request(
            "GET",
            "/api/programs",
            token=self.student_token,
            params={"instituteId": self.institute_id},
        )
        self.expect(programs, 200, "programs")
        program_items = programs.json()
        program = next((item for item in program_items if "BIM" in item.get("name", "")), None)
        program = program or (program_items[0] if program_items else None)
        if not program:
            raise SmokeFailure("programs returned no items")
        self.program_id = str(program["id"])

    def onboarding(self) -> None:
        response = self.request(
            "POST",
            "/api/onboarding",
            token=self.student_token,
            json={
                "universityId": self.university_id,
                "instituteId": self.institute_id,
                "courseId": self.program_id,
                "studyYear": "3",
                "interests": ["BIM", "стажировки", self.topic],
                "skills": [
                    {"name": "BIM-моделирование", "level": 4},
                    {"name": "Revit", "level": 3},
                    {"name": "Проектная документация", "level": 3},
                ],
                "careerGoal": "BIM-координатор в строительстве",
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
            "/api/v1/subscriptions/",
            token=self.student_token,
            json={"topic": self.topic, "filters": {"topic": self.topic}, "active": True},
        )
        self.expect(response, 201, "create_subscription")
        if response.json().get("topic") != self.topic:
            raise SmokeFailure("subscription topic was not persisted")
        self.subscription_id = str(response.json().get("id") or "")
        if not self.subscription_id:
            raise SmokeFailure("subscription creation did not return an id")

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

    def open_published_opportunity(self) -> None:
        response = self.request(
            "GET",
            f"/api/student/opportunities/{self.opportunity_id}",
            token=self.student_token,
        )
        self.expect(response, 200, "open_published_opportunity")
        opportunity = response.json()
        if str(opportunity.get("id")) != self.opportunity_id:
            raise SmokeFailure("opened opportunity does not match the notification")
        if self.topic not in opportunity.get("requirements", []):
            raise SmokeFailure("opened opportunity is not relevant to the student's subscription")

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

    def cleanup_test_data(self) -> None:
        if self.opportunity_id:
            response = self.request(
                "DELETE",
                f"/api/admin/opportunities/{self.opportunity_id}",
                token=self.admin_token,
            )
            self.expect(response, 204, "delete_test_opportunity")
        if self.subscription_id:
            response = self.request(
                "DELETE",
                f"/api/v1/subscriptions/{self.subscription_id}/",
                token=self.student_token,
            )
            self.expect(response, 204, "delete_test_subscription")

    def opportunity_payload(self) -> dict[str, Any]:
        return {
            "title": f"Проверочная возможность {self.topic}",
            "company": "Карьерный центр МГСУ",
            "description": f"Проверка подписки и уведомлений для {self.topic}.",
            "type": "internship",
            "location": "Москва / кампус",
            "remote": True,
            "requirements": [self.topic],
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
