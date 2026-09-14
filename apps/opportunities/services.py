"""
Opportunity Matching Service

Provides deterministic, explainable matching between student profiles and opportunities.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MatchResult:
    """
    Result of matching a student profile to an opportunity.

    Attributes:
        score: Overall match score (0-100)
        reasons: List of positive match reasons
        gaps: List of gaps or missing requirements
        component_scores: Breakdown of individual scoring components
    """
    score: float
    reasons: List[str]
    gaps: List[str]
    component_scores: Dict[str, float]


class OpportunityMatchingService:
    """
    Service for matching student profiles with opportunities.

    Scoring Algorithm:
    - Skill Match (40%): How well student skills align with required/preferred skills
    - Audience Match (25%): Whether student fits target audience criteria
    - Interest Match (20%): Alignment between student interests and opportunity domain
    - Career Goal Match (15%): How well opportunity supports career aspirations

    Score ranges:
    - 80-100: Excellent match
    - 60-79: Good match
    - 40-59: Moderate match
    - 20-39: Weak match
    - 0-19: Poor match

    Examples:
        >>> service = OpportunityMatchingService()
        >>> student = {
        ...     'skills': ['Python', 'Machine Learning', 'Data Analysis'],
        ...     'grade_level': 11,
        ...     'interests': ['AI', 'Technology', 'Research'],
        ...     'career_goals': ['Data Scientist', 'AI Researcher'],
        ...     'gpa': 3.8
        ... }
        >>> opportunity = {
        ...     'required_skills': ['Python'],
        ...     'preferred_skills': ['Machine Learning', 'Statistics'],
        ...     'target_audience': {'min_grade': 10, 'max_grade': 12},
        ...     'domains': ['Technology', 'AI', 'Research'],
        ...     'related_careers': ['Data Scientist', 'Software Engineer']
        ... }
        >>> result = service.calculate_match(student, opportunity)
        >>> result.score >= 80  # Excellent match
        True
        >>> 'Strong skill alignment' in result.reasons
        True
    """

    # Scoring weights
    SKILL_WEIGHT = 0.40
    AUDIENCE_WEIGHT = 0.25
    INTEREST_WEIGHT = 0.20
    CAREER_WEIGHT = 0.15

    def calculate_match(
        self,
        student_profile: Dict,
        opportunity: Dict,
        save_to_db: bool = False
    ) -> MatchResult:
        """
        Calculate match score between student profile and opportunity.

        Args:
            student_profile: Dictionary with student data
                - skills: List[str] - Student's skills
                - grade_level: int - Current grade
                - interests: List[str] - Areas of interest
                - career_goals: List[str] - Career aspirations
                - gpa: float (optional) - Grade point average
            opportunity: Dictionary with opportunity data
                - required_skills: List[str] - Must-have skills
                - preferred_skills: List[str] - Nice-to-have skills
                - target_audience: Dict - Audience criteria
                - domains: List[str] - Opportunity domains
                - related_careers: List[str] - Related career paths
            save_to_db: Whether to persist MatchResult to database

        Returns:
            MatchResult with score, reasons, gaps, and component scores
        """
        reasons = []
        gaps = []
        component_scores = {}

        # 1. Calculate Skill Match (40%)
        skill_score, skill_reasons, skill_gaps = self._calculate_skill_match(
            student_profile.get('skills', []),
            opportunity.get('required_skills', []),
            opportunity.get('preferred_skills', [])
        )
        component_scores['skill_match'] = skill_score
        reasons.extend(skill_reasons)
        gaps.extend(skill_gaps)

        # 2. Calculate Audience Match (25%)
        audience_score, audience_reasons, audience_gaps = self._calculate_audience_match(
            student_profile,
            opportunity.get('target_audience', {})
        )
        component_scores['audience_match'] = audience_score
        reasons.extend(audience_reasons)
        gaps.extend(audience_gaps)

        # 3. Calculate Interest Match (20%)
        interest_score, interest_reasons, interest_gaps = self._calculate_interest_match(
            student_profile.get('interests', []),
            opportunity.get('domains', [])
        )
        component_scores['interest_match'] = interest_score
        reasons.extend(interest_reasons)
        gaps.extend(interest_gaps)

        # 4. Calculate Career Goal Match (15%)
        career_score, career_reasons, career_gaps = self._calculate_career_goal_match(
            student_profile.get('career_goals', []),
            opportunity.get('related_careers', [])
        )
        component_scores['career_goal_match'] = career_score
        reasons.extend(career_reasons)
        gaps.extend(career_gaps)

        # Calculate weighted overall score
        overall_score = (
            skill_score * self.SKILL_WEIGHT +
            audience_score * self.AUDIENCE_WEIGHT +
            interest_score * self.INTEREST_WEIGHT +
            career_score * self.CAREER_WEIGHT
        )

        result = MatchResult(
            score=round(overall_score, 2),
            reasons=reasons,
            gaps=gaps,
            component_scores=component_scores
        )

        if save_to_db:
            self._save_match_result(student_profile, opportunity, result)

        return result

    def _calculate_skill_match(
        self,
        student_skills: List[str],
        required_skills: List[str],
        preferred_skills: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculate skill match score.

        Formula:
        - All required skills met: 60 base points
        - Each missing required skill: -20 points
        - Each preferred skill met: +5 points (up to 40 points)
        """
        reasons = []
        gaps = []
        score = 0.0

        # Normalize skills to lowercase for comparison
        student_skills_normalized = {s.lower().strip() for s in student_skills}
        required_normalized = {s.lower().strip() for s in required_skills}
        preferred_normalized = {s.lower().strip() for s in preferred_skills}

        # Check required skills
        if required_normalized:
            matched_required = student_skills_normalized & required_normalized
            missing_required = required_normalized - student_skills_normalized

            if len(missing_required) == 0:
                score = 60.0
                reasons.append(f"All {len(required_normalized)} required skills met")
            else:
                # Penalty for missing required skills
                score = max(0, 60 - (len(missing_required) * 20))
                if len(matched_required) > 0:
                    reasons.append(f"{len(matched_required)}/{len(required_normalized)} required skills met")
                for skill in list(missing_required)[:3]:  # Limit to 3 for brevity
                    gaps.append(f"Missing required skill: {skill}")
        else:
            # No required skills specified
            score = 60.0

        # Check preferred skills (bonus points)
        if preferred_normalized:
            matched_preferred = student_skills_normalized & preferred_normalized
            preferred_bonus = min(40.0, len(matched_preferred) * 5.0)
            score += preferred_bonus

            if len(matched_preferred) > 0:
                reasons.append(f"{len(matched_preferred)} preferred skills matched")

            missing_preferred = preferred_normalized - student_skills_normalized
            if len(missing_preferred) > 0 and len(missing_preferred) <= 2:
                for skill in missing_preferred:
                    gaps.append(f"Preferred skill: {skill}")

        return min(100.0, score), reasons, gaps

    def _calculate_audience_match(
        self,
        student_profile: Dict,
        target_audience: Dict
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculate audience match score.

        Checks:
        - Grade level range (if specified)
        - GPA requirement (if specified)
        - Other demographic criteria (if specified)
        """
        reasons = []
        gaps = []
        score = 100.0  # Start with full score, deduct for mismatches

        # Check grade level
        grade_level = student_profile.get('grade_level')
        min_grade = target_audience.get('min_grade')
        max_grade = target_audience.get('max_grade')

        if grade_level is not None:
            if min_grade is not None and grade_level < min_grade:
                score -= 40.0
                gaps.append(f"Grade level {grade_level} below minimum {min_grade}")
            elif max_grade is not None and grade_level > max_grade:
                score -= 40.0
                gaps.append(f"Grade level {grade_level} above maximum {max_grade}")
            else:
                reasons.append("Grade level matches target audience")

        # Check GPA requirement
        gpa = student_profile.get('gpa')
        min_gpa = target_audience.get('min_gpa')

        if min_gpa is not None and gpa is not None:
            if gpa >= min_gpa:
                reasons.append(f"GPA {gpa} meets requirement ({min_gpa}+)")
            else:
                score -= 30.0
                gaps.append(f"GPA {gpa} below requirement {min_gpa}")

        # Check location (if specified)
        student_location = student_profile.get('location')
        target_locations = target_audience.get('locations', [])

        if target_locations and student_location:
            location_match = any(
                loc.lower() in student_location.lower()
                for loc in target_locations
            )
            if location_match:
                reasons.append("Location matches opportunity")
            else:
                score -= 20.0
                gaps.append(f"Location preference: {', '.join(target_locations)}")

        return max(0.0, score), reasons, gaps

    def _calculate_interest_match(
        self,
        student_interests: List[str],
        opportunity_domains: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculate interest match score.

        Formula:
        - Base score: 50 points
        - Each matching interest/domain: +25 points (up to 50 bonus)
        """
        reasons = []
        gaps = []

        if not opportunity_domains:
            return 75.0, ["No specific domain requirements"], []

        # Normalize for comparison
        interests_normalized = {i.lower().strip() for i in student_interests}
        domains_normalized = {d.lower().strip() for d in opportunity_domains}

        # Check for direct matches
        direct_matches = interests_normalized & domains_normalized

        # Check for partial matches (substring matching)
        partial_matches = set()
        for interest in interests_normalized:
            for domain in domains_normalized:
                if interest in domain or domain in interest:
                    partial_matches.add(domain)

        total_matches = direct_matches | partial_matches

        if len(total_matches) == 0:
            score = 30.0
            gaps.append(f"Consider exploring: {', '.join(list(domains_normalized)[:3])}")
        else:
            score = 50.0 + min(50.0, len(total_matches) * 25.0)
            match_list = ', '.join(list(total_matches)[:3])
            reasons.append(f"Strong interest alignment: {match_list}")

        return score, reasons, gaps

    def _calculate_career_goal_match(
        self,
        career_goals: List[str],
        related_careers: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculate career goal match score.

        Formula:
        - Any career goal matches related careers: 100 points
        - Partial keyword match: 60 points
        - No match: 40 points (still some value for exploration)
        """
        reasons = []
        gaps = []

        if not related_careers:
            return 70.0, ["Opportunity provides general career development"], []

        if not career_goals:
            return 50.0, [], ["Career goals not specified"]

        # Normalize
        goals_normalized = {g.lower().strip() for g in career_goals}
        careers_normalized = {c.lower().strip() for c in related_careers}

        # Check for direct matches
        direct_matches = goals_normalized & careers_normalized

        if direct_matches:
            match_list = ', '.join(list(direct_matches)[:2])
            reasons.append(f"Aligns with career goal: {match_list}")
            return 100.0, reasons, gaps

        # Check for partial keyword matches
        partial_matches = []
        for goal in goals_normalized:
            goal_keywords = set(goal.split())
            for career in careers_normalized:
                career_keywords = set(career.split())
                if goal_keywords & career_keywords:
                    partial_matches.append(career)
                    break

        if partial_matches:
            reasons.append(f"Related to career path: {partial_matches[0]}")
            return 60.0, reasons, gaps

        # No match, but still has exploratory value
        gaps.append(f"Opportunity relates to: {', '.join(list(careers_normalized)[:2])}")
        return 40.0, reasons, gaps

    def _save_match_result(
        self,
        student_profile: Dict,
        opportunity: Dict,
        result: MatchResult
    ) -> None:
        """
        Save match result to database.

        Note: Actual implementation would use Django ORM models.
        This is a placeholder for the database integration.
        """
        # TODO: Implement database persistence
        # Example:
        # from apps.opportunities.models import OpportunityMatch
        #
        # OpportunityMatch.objects.create(
        #     student_id=student_profile.get('id'),
        #     opportunity_id=opportunity.get('id'),
        #     score=result.score,
        #     reasons=result.reasons,
        #     gaps=result.gaps,
        #     component_scores=result.component_scores,
        #     matched_at=datetime.now()
        # )
        pass

    def batch_calculate_matches(
        self,
        student_profile: Dict,
        opportunities: List[Dict],
        min_score: float = 0.0
    ) -> List[Tuple[Dict, MatchResult]]:
        """
        Calculate matches for multiple opportunities and return sorted results.

        Args:
            student_profile: Student profile dictionary
            opportunities: List of opportunity dictionaries
            min_score: Minimum score threshold to include in results

        Returns:
            List of (opportunity, match_result) tuples, sorted by score descending
        """
        results = []

        for opportunity in opportunities:
            match_result = self.calculate_match(student_profile, opportunity)
            if match_result.score >= min_score:
                results.append((opportunity, match_result))

        # Sort by score descending
        results.sort(key=lambda x: x[1].score, reverse=True)

        return results
