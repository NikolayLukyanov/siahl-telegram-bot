"""Team scraper for SIAHL league data.

Scrapes team standings, divisions, and basic team information from the SIAHL website.
"""

import re
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup, Tag
from loguru import logger

from src.config import settings
from src.services.scraper.base_scraper import BaseScraper


class TeamScraper(BaseScraper):
    """Scraper for SIAHL team standings and information."""

    def __init__(self) -> None:
        """Initialize team scraper with SIAHL base URL."""
        super().__init__()

    async def get_all_teams(
        self,
        league_id: Optional[int] = None,
        season: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch all teams from the league standings page.

        Args:
            league_id: SIAHL league ID (default from settings)
            season: Season ID (default from settings)

        Returns:
            List of team dictionaries with standings data

        Example return:
            [
                {
                    'team_id': 4784,
                    'name': 'San Jose Sharks',
                    'division': 'Adult Division 1',
                    'games_played': 12,
                    'wins': 8,
                    'losses': 3,
                    'ties': 0,
                    'overtime_losses': 1,
                    'points': 17,
                    'streak': 'W3',
                    'tie_breaker': 'GF: 45',
                    'league_id': 1,
                    'season': 72
                },
                ...
            ]
        """
        league_id = league_id or settings.default_league_id
        season = season or settings.current_season

        url = f"{self.base_url}/display-stats.php"
        params = {"league": league_id}

        logger.info(f"Fetching teams for league {league_id}, season {season}")

        try:
            html = await self._fetch_html(url, params=params)
            soup = BeautifulSoup(html, "lxml")

            teams = []

            # Find all tables (standings tables)
            tables = soup.find_all("table")
            logger.debug(f"Found {len(tables)} tables on page")

            for table in tables:
                # Look for division name before the table
                # Try to find text containing "Division" in elements before this table
                division = self._find_division_name(table)

                if division:
                    logger.debug(f"Found division: {division}")
                    division_teams = self._parse_standings_table(
                        table,
                        division=division,
                        league_id=league_id,
                        season=season,
                    )
                    teams.extend(division_teams)
                else:
                    logger.warning(f"Could not find division name for table")

            logger.info(f"Successfully scraped {len(teams)} teams from {len(set(t['division'] for t in teams))} divisions")
            return teams

        except Exception as e:
            logger.error(f"Failed to scrape teams: {e}")
            raise

    def _find_division_name(self, table: Tag) -> Optional[str]:
        """
        Find the division name for a table by looking at preceding elements.

        Args:
            table: BeautifulSoup table element

        Returns:
            Division name string, or None if not found
        """
        # Look at previous siblings for text containing "Division"
        current = table.previous_sibling

        # Search up to 10 previous siblings
        for _ in range(10):
            if current is None:
                break

            # Check if this element has text containing "Division"
            if hasattr(current, 'get_text'):
                text = current.get_text(strip=True)
                if text and "Division" in text:
                    logger.debug(f"Found division in previous sibling: {text}")
                    return text

            current = current.previous_sibling

        # If not found in siblings, try looking at parent's previous siblings
        parent = table.parent
        if parent:
            current = parent.previous_sibling
            for _ in range(5):
                if current is None:
                    break

                if hasattr(current, 'get_text'):
                    text = current.get_text(strip=True)
                    if text and "Division" in text:
                        logger.debug(f"Found division in parent's sibling: {text}")
                        return text

                current = current.previous_sibling

        return None

    def _parse_standings_table(
        self,
        table: Tag,
        division: str,
        league_id: int,
        season: int,
    ) -> list[dict[str, Any]]:
        """
        Parse a single standings table for a division.

        Args:
            table: BeautifulSoup table element
            division: Division name
            league_id: League ID
            season: Season ID

        Returns:
            List of team dictionaries
        """
        teams = []

        # Find all data rows (skip header)
        rows = table.find_all("tr")
        if not rows:
            return teams

        # First row is header, skip it
        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) < 8:  # Need at least 8 columns
                continue

            try:
                # Extract team name and ID from link
                team_link = cells[0].find("a")
                if not team_link:
                    continue

                team_name = team_link.get_text(strip=True)
                team_id = self._extract_team_id(team_link.get("href", ""))

                if not team_id:
                    logger.warning(f"Could not extract team ID for {team_name}")
                    continue

                # Parse standings data
                team_data = {
                    "team_id": team_id,
                    "name": team_name,
                    "division": division,
                    "games_played": self._safe_int(cells[1].get_text(strip=True)),
                    "wins": self._safe_int(cells[2].get_text(strip=True)),
                    "losses": self._safe_int(cells[3].get_text(strip=True)),
                    "ties": self._safe_int(cells[4].get_text(strip=True)),
                    "overtime_losses": self._safe_int(cells[5].get_text(strip=True)),
                    "points": self._safe_int(cells[6].get_text(strip=True)),
                    "streak": cells[7].get_text(strip=True) if len(cells) > 7 else None,
                    "tie_breaker": cells[8].get_text(strip=True) if len(cells) > 8 else None,
                    "league_id": league_id,
                    "season": season,
                }

                teams.append(team_data)
                logger.debug(f"Parsed team: {team_name} ({team_id}) - {team_data['wins']}-{team_data['losses']}-{team_data['ties']}")

            except Exception as e:
                logger.warning(f"Failed to parse team row: {e}")
                continue

        return teams

    def _extract_team_id(self, href: str) -> Optional[int]:
        """
        Extract team ID from a link href.

        Args:
            href: Link URL (e.g., 'display-schedule?team=4784&season=72&league=1')

        Returns:
            Team ID as integer, or None if not found
        """
        if not href:
            return None

        try:
            # Parse query parameters
            if "?" in href:
                query_string = href.split("?", 1)[1]
                params = parse_qs(query_string)
                team_id_list = params.get("team", [])
                if team_id_list:
                    return int(team_id_list[0])
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to extract team ID from href '{href}': {e}")

        return None

    @staticmethod
    def _safe_int(value: str) -> int:
        """
        Safely convert string to integer.

        Args:
            value: String value to convert

        Returns:
            Integer value, or 0 if conversion fails
        """
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    async def get_team_details(
        self,
        team_id: int,
        season: Optional[int] = None,
        league_id: Optional[int] = None,
        stat_class: int = 1,
    ) -> dict[str, Any]:
        """
        Fetch detailed team information and statistics.

        Args:
            team_id: Team ID
            season: Season ID (default from settings)
            league_id: League ID (default from settings)
            stat_class: Stat class (default 1)

        Returns:
            Dictionary with team details

        Note:
            This is a placeholder for Phase 2. Will scrape:
            - Full roster with player stats
            - Team statistics (GF, GA, PP%, PK%, etc.)
            - Recent game results
        """
        season = season or settings.current_season
        league_id = league_id or settings.default_league_id

        url = f"{self.base_url}/display-schedule"
        params = {
            "team": team_id,
            "season": season,
            "league": league_id,
            "stat_class": stat_class,
        }

        logger.info(f"Fetching details for team {team_id}")

        try:
            html = await self._fetch_html(url, params=params)
            # TODO: Implement detailed parsing in Phase 2
            # For now, just return basic structure
            return {
                "team_id": team_id,
                "season": season,
                "league_id": league_id,
                "html_content": html,  # Store for later parsing
            }

        except Exception as e:
            logger.error(f"Failed to scrape team details for {team_id}: {e}")
            raise
