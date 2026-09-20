from __future__ import annotations

from typing import Any

from django.db.models import Q
from django.utils import timezone

from apps.analytics.models import InteractionEvent

from .models import KnowledgeItem


class KnowledgeSearchService:
    """Deterministic verified knowledge search with safe fallback."""

    fallback_message = 'Не найден подтвержденный актуальный материал.'

    def search(self, query: str, user, limit: int = 5) -> dict[str, Any]:
        clean_query = (query or '').strip()
        university = getattr(user, 'university', '') or 'НИУ МГСУ'
        profile = getattr(user, 'student_profile', None)

        if not clean_query:
            return self._fallback(university, user, clean_query)

        today = timezone.now().date()
        queryset = KnowledgeItem.objects.filter(
            university=university,
            published=True,
            verified_status='verified',
        ).filter(
            Q(actual_until__isnull=True) | Q(actual_until__gte=today)
        )

        audience = set(self._audience(profile))

        tokens = [token.lower() for token in clean_query.split() if len(token) >= 3]
        if tokens:
            token_filter = Q()
            for token in tokens:
                token_filter |= Q(title__icontains=token) | Q(content__icontains=token)
            queryset = queryset.filter(token_filter)
        else:
            queryset = queryset.filter(Q(title__icontains=clean_query) | Q(content__icontains=clean_query))

        visible_items = [
            item for item in queryset[:50]
            if self._matches_audience(item.audience or [], audience)
        ]
        ranked = sorted(
            visible_items,
            key=lambda item: self._score(item, clean_query, tokens),
            reverse=True,
        )[:limit]

        if not ranked:
            self._log(university, user, 'knowledge_no_answer', clean_query, 0)
            return self._fallback(university, user, clean_query)

        results = [self._serialize(item, self._score(item, clean_query, tokens)) for item in ranked]
        self._log(university, user, 'knowledge_search', clean_query, len(results))
        return {
            'found': True,
            'query': clean_query,
            'results': results,
            'answer': results[0],
        }

    def _score(self, item: KnowledgeItem, query: str, tokens: list[str]) -> int:
        title = item.title.lower()
        content = item.content.lower()
        score = 0
        if query.lower() in title:
            score += 10
        if query.lower() in content:
            score += 5
        for token in tokens:
            if token in title:
                score += 3
            if token in content:
                score += 1
        return score

    def _audience(self, profile) -> list[str]:
        values = ['all', 'students']
        if not profile:
            return values
        if profile.course == 1:
            values.append('freshmen')
        if profile.course and profile.course >= 4:
            values.append('graduates')
        if profile.institute:
            values.append(profile.institute)
        return values

    def _serialize(self, item: KnowledgeItem, score: int) -> dict[str, Any]:
        return {
            'id': str(item.id),
            'title': item.title,
            'content': item.content,
            'source_url': item.source_url,
            'responsible_unit': item.responsible_unit,
            'audience': item.audience,
            'verified_status': item.verified_status,
            'actual_until': item.actual_until.isoformat() if item.actual_until else None,
            'updated_at': item.updated_at.isoformat(),
            'relevance_score': score,
        }

    def _matches_audience(self, item_audience: list[str], audience: set[str]) -> bool:
        if not item_audience:
            return True
        normalized = {str(value) for value in item_audience}
        return bool(normalized & audience)

    def _fallback(self, university: str, user, query: str) -> dict[str, Any]:
        return {
            'found': False,
            'query': query,
            'message': self.fallback_message,
            'escalation': {
                'unit': 'Учебный офис',
                'contact': f'helpdesk@{self._slug(university)}.local',
            },
            'results': [],
        }

    def _log(self, university: str, user, event_type: str, query: str, result_count: int) -> None:
        InteractionEvent.objects.create(
            university=university,
            user=user if getattr(user, 'is_authenticated', False) else None,
            event_type=event_type,
            entity_type='knowledge',
            metadata={'query': query, 'result_count': result_count},
        )

    def _slug(self, value: str) -> str:
        return ''.join(char.lower() for char in value if char.isalnum()) or 'demo'
