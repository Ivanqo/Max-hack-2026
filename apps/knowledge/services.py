"""
Knowledge search service for finding relevant knowledge items.

Provides comprehensive search functionality with PostgreSQL full-text search,
trigram similarity, and intelligent filtering by university, audience, and verification status.
"""

import logging
from typing import Dict, List, Optional, Any
from django.db.models import Q, QuerySet, F
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.utils import timezone

from backend.apps.knowledge.models import KnowledgeItem
from backend.apps.analytics.models import InteractionEvent


logger = logging.getLogger(__name__)


class KnowledgeSearchService:
    """
    Service for searching knowledge items with PostgreSQL full-text search and trigram similarity.

    Provides intelligent search with:
    - Full-text search on title and content
    - Trigram similarity for fuzzy matching
    - Filtering by university, verification status, audience
    - Fallback logic when no results found
    - Analytics event logging
    """

    # Search configuration constants
    MIN_FULLTEXT_RANK = 0.01  # Minimum rank threshold for full-text search
    MIN_TRIGRAM_SIMILARITY = 0.2  # Minimum similarity for trigram matching
    MAX_RESULTS = 50  # Maximum number of results to return

    # Weight configuration for search ranking
    TITLE_WEIGHT = 'A'  # Highest weight for title matches
    CONTENT_WEIGHT = 'B'  # Lower weight for content matches

    def __init__(self):
        """Initialize the knowledge search service."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def search(
        self,
        query: str,
        university: str,
        student_profile: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        limit: int = MAX_RESULTS
    ) -> Dict[str, Any]:
        """
        Search for knowledge items matching the query.

        Performs a multi-stage search:
        1. Full-text search with filters (university, published, verified, audience)
        2. If no results, retry with trigram similarity
        3. If still no results, return escalation information

        Args:
            query: Search query string from the user
            university: University name to filter results
            student_profile: Optional student profile dict with keys:
                - course: Year of study (1-6)
                - program: Study program
                - interests: List of interests
                - career_goal: Career goal name
            user_id: Optional user ID for analytics logging
            limit: Maximum number of results (default: MAX_RESULTS)

        Returns:
            Dictionary containing:
            - results: List of matching knowledge items with fields:
                - id: Knowledge item ID
                - title: Item title
                - content: Item content (markdown)
                - source_url: Optional source URL
                - responsible_unit: Department/unit responsible
                - verified_status: Verification status
                - updated_at: Last update timestamp
                - relevance_score: Search relevance score
            - total_count: Total number of results
            - search_method: Method used ('fulltext', 'trigram', or 'none')
            - escalation_info: Present only when no results found, contains:
                - message: User-facing message
                - suggested_contact: Contact information for help

        Example:
            >>> service = KnowledgeSearchService()
            >>> profile = {'course': 2, 'program': 'Computer Science'}
            >>> results = service.search(
            ...     query="scholarship deadlines",
            ...     university="MIT",
            ...     student_profile=profile,
            ...     user_id=123
            ... )
            >>> print(results['total_count'])
            5
            >>> print(results['search_method'])
            'fulltext'
        """
        self.logger.info(
            f"Knowledge search initiated: query='{query}', university='{university}', "
            f"user_id={user_id}"
        )

        # Validate inputs
        if not query or not query.strip():
            self.logger.warning("Empty query provided")
            return self._empty_result_with_escalation(university, user_id)

        if not university or not university.strip():
            self.logger.warning("Empty university provided")
            return self._empty_result_with_escalation(university, user_id)

        query = query.strip()
        university = university.strip()

        # Determine target audience from student profile
        audience_filters = self._determine_audience_filters(student_profile)

        # Stage 1: Full-text search
        results = self._fulltext_search(query, university, audience_filters, limit)

        if results:
            self.logger.info(f"Full-text search found {len(results)} results")
            serialized = self._serialize_results(results, 'fulltext')
            self._log_search_event(
                university=university,
                user_id=user_id,
                query=query,
                result_count=len(results),
                search_method='fulltext'
            )
            return serialized

        # Stage 2: Trigram similarity search (fuzzy matching)
        self.logger.info("No full-text results, trying trigram similarity")
        results = self._trigram_search(query, university, audience_filters, limit)

        if results:
            self.logger.info(f"Trigram search found {len(results)} results")
            serialized = self._serialize_results(results, 'trigram')
            self._log_search_event(
                university=university,
                user_id=user_id,
                query=query,
                result_count=len(results),
                search_method='trigram'
            )
            return serialized

        # Stage 3: No results found - return escalation info
        self.logger.warning(f"No results found for query: '{query}'")
        self._log_no_answer_event(university, user_id, query)
        return self._empty_result_with_escalation(university, user_id)

    def _fulltext_search(
        self,
        query: str,
        university: str,
        audience_filters: List[str],
        limit: int
    ) -> QuerySet:
        """
        Perform PostgreSQL full-text search.

        Args:
            query: Search query string
            university: University name filter
            audience_filters: List of audience types to match
            limit: Maximum results

        Returns:
            QuerySet of KnowledgeItem objects ordered by relevance
        """
        # Create search vector with weighted fields
        search_vector = (
            SearchVector('title', weight=self.TITLE_WEIGHT) +
            SearchVector('content', weight=self.CONTENT_WEIGHT)
        )

        # Create search query
        search_query = SearchQuery(query, search_type='websearch')

        # Build base queryset with filters
        queryset = KnowledgeItem.objects.filter(
            university__iexact=university,
            published=True,
            verified_status='verified'
        )

        # Check if knowledge items are still current (not expired)
        today = timezone.now().date()
        queryset = queryset.filter(
            Q(actual_until__isnull=True) | Q(actual_until__gte=today)
        )

        # Apply audience filters
        if audience_filters:
            audience_q = Q(audience__contains=['all'])
            for audience in audience_filters:
                audience_q |= Q(audience__contains=[audience])
            queryset = queryset.filter(audience_q)

        # Apply full-text search with ranking
        queryset = queryset.annotate(
            rank=SearchRank(search_vector, search_query)
        ).filter(
            rank__gte=self.MIN_FULLTEXT_RANK
        ).order_by('-rank')

        return queryset[:limit]

    def _trigram_search(
        self,
        query: str,
        university: str,
        audience_filters: List[str],
        limit: int
    ) -> QuerySet:
        """
        Perform PostgreSQL trigram similarity search for fuzzy matching.

        Useful when full-text search returns no results due to typos or
        partial matches.

        Args:
            query: Search query string
            university: University name filter
            audience_filters: List of audience types to match
            limit: Maximum results

        Returns:
            QuerySet of KnowledgeItem objects ordered by similarity
        """
        # Build base queryset with filters
        queryset = KnowledgeItem.objects.filter(
            university__iexact=university,
            published=True,
            verified_status='verified'
        )

        # Check if knowledge items are still current
        today = timezone.now().date()
        queryset = queryset.filter(
            Q(actual_until__isnull=True) | Q(actual_until__gte=today)
        )

        # Apply audience filters
        if audience_filters:
            audience_q = Q(audience__contains=['all'])
            for audience in audience_filters:
                audience_q |= Q(audience__contains=[audience])
            queryset = queryset.filter(audience_q)

        # Calculate trigram similarity for both title and content
        queryset = queryset.annotate(
            title_similarity=TrigramSimilarity('title', query),
            content_similarity=TrigramSimilarity('content', query)
        ).annotate(
            # Combined similarity score (title weighted higher)
            similarity=F('title_similarity') * 2 + F('content_similarity')
        ).filter(
            similarity__gte=self.MIN_TRIGRAM_SIMILARITY
        ).order_by('-similarity')

        return queryset[:limit]

    def _determine_audience_filters(
        self,
        student_profile: Optional[Dict[str, Any]]
    ) -> List[str]:
        """
        Determine appropriate audience filters based on student profile.

        Args:
            student_profile: Student profile dictionary or None

        Returns:
            List of audience types that match the student profile
        """
        if not student_profile:
            return ['all', 'students']

        audience = ['all', 'students']

        # Add course-based audience
        course = student_profile.get('course')
        if course == 1:
            audience.append('freshmen')
        elif course and course >= 4:
            audience.append('graduates')

        # Note: International/local status would need to be added to student profile
        # For now, we include both to not over-filter

        return audience

    def _serialize_results(
        self,
        queryset: QuerySet,
        search_method: str
    ) -> Dict[str, Any]:
        """
        Serialize queryset results into response dictionary.

        Args:
            queryset: QuerySet of KnowledgeItem objects
            search_method: Search method used ('fulltext' or 'trigram')

        Returns:
            Dictionary with results, count, and search method
        """
        results = []
        for item in queryset:
            # Get relevance score from annotation
            if search_method == 'fulltext':
                relevance_score = float(getattr(item, 'rank', 0))
            else:  # trigram
                relevance_score = float(getattr(item, 'similarity', 0))

            results.append({
                'id': item.id,
                'title': item.title,
                'content': item.content,
                'source_url': item.source_url or None,
                'responsible_unit': item.responsible_unit or None,
                'verified_status': item.verified_status,
                'updated_at': item.updated_at.isoformat(),
                'relevance_score': round(relevance_score, 4)
            })

        return {
            'results': results,
            'total_count': len(results),
            'search_method': search_method
        }

    def _empty_result_with_escalation(
        self,
        university: str,
        user_id: Optional[int]
    ) -> Dict[str, Any]:
        """
        Generate empty result response with escalation information.

        Args:
            university: University name
            user_id: Optional user ID

        Returns:
            Dictionary with empty results and escalation info
        """
        return {
            'results': [],
            'total_count': 0,
            'search_method': 'none',
            'escalation_info': {
                'message': (
                    "Sorry, I couldn't find an answer to your question in our knowledge base. "
                    "Your question has been forwarded to our support team, and they will "
                    "get back to you soon."
                ),
                'suggested_contact': self._get_university_contact(university)
            }
        }

    def _get_university_contact(self, university: str) -> str:
        """
        Get contact information for university support.

        In a real implementation, this would look up university-specific
        contact information from a configuration or database.

        Args:
            university: University name

        Returns:
            Contact information string
        """
        # This is a placeholder implementation
        # In production, fetch from a university contacts table or config
        return f"Please contact your university support team or visit the {university} help desk."

    def _log_search_event(
        self,
        university: str,
        user_id: Optional[int],
        query: str,
        result_count: int,
        search_method: str
    ) -> None:
        """
        Log a knowledge search event to analytics.

        Args:
            university: University name
            user_id: Optional user ID
            query: Search query
            result_count: Number of results found
            search_method: Search method used
        """
        try:
            InteractionEvent.objects.create(
                university=university,
                user_id=user_id,
                event_type='search',
                entity_type='knowledge',
                entity_id=None,
                metadata={
                    'query': query,
                    'result_count': result_count,
                    'search_method': search_method,
                    'event_name': 'knowledge_search'
                }
            )
            self.logger.debug(f"Logged knowledge_search event for user {user_id}")
        except Exception as e:
            # Don't fail the search if logging fails
            self.logger.error(f"Failed to log search event: {e}", exc_info=True)

    def _log_no_answer_event(
        self,
        university: str,
        user_id: Optional[int],
        query: str
    ) -> None:
        """
        Log a no-answer event when search returns no results.

        This helps identify gaps in the knowledge base.

        Args:
            university: University name
            user_id: Optional user ID
            query: Search query that returned no results
        """
        try:
            InteractionEvent.objects.create(
                university=university,
                user_id=user_id,
                event_type='search',
                entity_type='knowledge',
                entity_id=None,
                metadata={
                    'query': query,
                    'result_count': 0,
                    'event_name': 'knowledge_no_answer',
                    'requires_escalation': True
                }
            )
            self.logger.debug(f"Logged knowledge_no_answer event for user {user_id}")
        except Exception as e:
            # Don't fail the search if logging fails
            self.logger.error(f"Failed to log no-answer event: {e}", exc_info=True)
