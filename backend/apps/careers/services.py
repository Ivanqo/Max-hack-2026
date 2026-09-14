from __future__ import annotations

from typing import Any

from apps.careers.models import CareerRole
from apps.profiles.models import StudentProfile


class CareerGPSService:
    """Deterministic readiness calculation for a student and career role."""

    def calculate(self, student: StudentProfile, career_role: CareerRole) -> dict[str, Any]:
        required = list(career_role.required_skills.select_related('skill'))
        student_levels = {
            item.skill_id: item.level
            for item in student.skills.select_related('skill').all()
        }
        total_weight = sum(item.weight for item in required) or 1
        earned = 0.0
        strengths: list[str] = []
        gaps: list[dict[str, Any]] = []

        for item in required:
            current = student_levels.get(item.skill_id, 0)
            ratio = min(current / item.required_level, 1) if item.required_level else 0
            earned += ratio * item.weight

            if current >= item.required_level:
                strengths.append(
                    f'{item.skill.name}: уровень {current}/5 покрывает требуемый {item.required_level}/5'
                )
            else:
                missing = item.required_level - current
                gaps.append({
                    'skill': item.skill.name,
                    'current_level': current,
                    'required_level': item.required_level,
                    'missing_level': missing,
                    'priority': self._priority(missing, item.weight),
                })

        score = round((earned / total_weight) * 100)
        return {
            'career_role': career_role.name,
            'career_role_id': career_role.id,
            'readiness_score': score,
            'strengths': strengths,
            'gaps': gaps,
            'next_actions': self._next_actions(gaps),
        }

    def _priority(self, missing: int, weight: float) -> str:
        if missing >= 3 or weight >= 2:
            return 'high'
        if missing == 2:
            return 'medium'
        return 'low'

    def _next_actions(self, gaps: list[dict[str, Any]]) -> list[str]:
        if not gaps:
            return [
                'Выбрать ближайшую релевантную стажировку или проект.',
                'Добавить доказательства навыков в профиль.',
            ]

        actions = [
            f"Подтянуть {gap['skill']} до уровня {gap['required_level']}/5."
            for gap in gaps[:3]
        ]
        actions.append('Сохранить opportunity, где можно закрыть самый важный gap.')
        return actions[:3]

