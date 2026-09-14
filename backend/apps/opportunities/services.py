from __future__ import annotations

from typing import Any

from django.utils import timezone

from apps.opportunities.models import MatchResult, Opportunity, OpportunitySkill


LEVELS = {
    'beginner': 2,
    'intermediate': 3,
    'advanced': 4,
    'expert': 5,
}


class OpportunityMatchingService:
    """Explainable deterministic matching for student opportunities."""

    def calculate_for_user(self, user, opportunity: Opportunity, save: bool = True) -> dict[str, Any]:
        profile = getattr(user, 'student_profile', None)
        if not profile:
            result = {
                'score': 0,
                'reasons': [],
                'gaps': ['Профиль студента не заполнен.'],
                'component_scores': {},
                'calculated_at': timezone.now().isoformat(),
            }
            return result

        student_skills = {
            item.skill.name.lower(): item.level
            for item in profile.skills.select_related('skill').all()
        }
        required = self._required_skills(opportunity)

        skill_score, skill_reasons, skill_gaps = self._skill_score(student_skills, required)
        audience_score, audience_reasons, audience_gaps = self._audience_score(profile, opportunity.audience or {})
        interest_score, interest_reasons = self._interest_score(profile.interests or [], opportunity)
        career_score, career_reasons = self._career_score(profile, opportunity)

        score = round(
            skill_score * 0.55 +
            audience_score * 0.20 +
            interest_score * 0.15 +
            career_score * 0.10
        )
        reasons = skill_reasons + audience_reasons + interest_reasons + career_reasons
        gaps = skill_gaps + audience_gaps
        result = {
            'score': max(0, min(100, score)),
            'reasons': reasons[:5],
            'gaps': gaps[:5],
            'component_scores': {
                'skill_match': round(skill_score),
                'audience_match': round(audience_score),
                'interest_match': round(interest_score),
                'career_goal_match': round(career_score),
            },
            'calculated_at': timezone.now().isoformat(),
        }

        if save:
            MatchResult.objects.update_or_create(
                student=user,
                opportunity=opportunity,
                defaults={
                    'score': result['score'],
                    'reasons': result['reasons'],
                    'gaps': result['gaps'],
                },
            )
        return result

    def rank_for_user(self, user, opportunities) -> list[tuple[Opportunity, dict[str, Any]]]:
        ranked = [(item, self.calculate_for_user(user, item)) for item in opportunities]
        ranked.sort(key=lambda pair: pair[1]['score'], reverse=True)
        return ranked

    def _required_skills(self, opportunity: Opportunity) -> list[dict[str, Any]]:
        linked = list(opportunity.required_skills.all())
        if linked:
            return [
                {
                    'name': item.skill,
                    'level': LEVELS.get(item.required_level, 3),
                    'weight': item.weight,
                }
                for item in linked
            ]

        lines = [line.strip() for line in opportunity.requirements.splitlines() if line.strip()]
        return [{'name': line, 'level': 3, 'weight': 1} for line in lines[:8]]

    def _skill_score(self, student_skills: dict[str, int], required: list[dict[str, Any]]):
        if not required:
            return 80.0, ['Нет жестких требований по навыкам.'], []

        total_weight = sum(item['weight'] for item in required) or 1
        earned = 0.0
        reasons: list[str] = []
        gaps: list[str] = []
        for item in required:
            name = item['name']
            current = student_skills.get(name.lower(), 0)
            needed = item['level']
            ratio = min(current / needed, 1) if needed else 1
            earned += ratio * item['weight']
            if current >= needed:
                reasons.append(f'Подходит {name}')
            else:
                gaps.append(f'Не хватает {name}: {current}/5 при требуемом {needed}/5')
        return (earned / total_weight) * 100, reasons, gaps

    def _audience_score(self, profile, audience: dict[str, Any]):
        score = 100.0
        reasons = ['Подходит по университету']
        gaps: list[str] = []

        courses = audience.get('courses') or audience.get('course')
        if courses:
            allowed = courses if isinstance(courses, list) else [courses]
            if profile.course not in [int(value) for value in allowed]:
                score -= 35
                gaps.append('Курс не входит в целевую аудиторию.')
            else:
                reasons.append('Подходит по курсу')

        institute = audience.get('institute')
        if institute and profile.institute and institute.lower() not in profile.institute.lower():
            score -= 25
            gaps.append('Opportunity рассчитана на другой институт.')

        return max(score, 0), reasons, gaps

    def _interest_score(self, interests: list[str], opportunity: Opportunity):
        if not interests:
            return 50.0, []
        text = self._opportunity_text(opportunity)
        matched = [interest for interest in interests if interest.lower() in text]
        if matched:
            return min(100.0, 45 + len(matched) * 25), [f"Совпадает с интересами: {', '.join(matched[:3])}"]
        return 35.0, []

    def _career_score(self, profile, opportunity: Opportunity):
        if not profile.career_goal:
            return 50.0, []
        goal = profile.career_goal.name.lower()
        text = self._opportunity_text(opportunity)
        tokens = [token for token in goal.replace('-', ' ').split() if len(token) > 2]
        if any(token in text for token in tokens):
            return 100.0, [f'Связано с карьерной целью: {profile.career_goal.name}']
        return 45.0, []

    def _opportunity_text(self, opportunity: Opportunity) -> str:
        audience = ' '.join(str(value) for value in (opportunity.audience or {}).values())
        return f'{opportunity.title} {opportunity.description} {opportunity.requirements} {audience} {opportunity.type}'.lower()
