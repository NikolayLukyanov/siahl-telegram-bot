"""Schedule scraper for SIAHL game schedules.

Scrapes game schedules, results, and match details from the SIAHL website.
"""

import re
from datetime import datetime
from typing import Any, Optional
from urllib.parse import parse_qs

from bs4 import BeautifulSoup, Tag
from loguru import logger

from src.config import settings
from src.services.scraper.base_scraper import BaseScraper


class ScheduleScraper(BaseScraper):
    """Scraper for SIAHL team schedules and game information."""

    def __init__(self) -> None:
        """Initialize schedule scraper with SIAHL base URL."""
        super().__init__(base_url=settings.siahl_base_url)

    async def get_team_schedule(
        self,
        team_id: int,
        season: Optional[int] = None,
        league_id: Optional[int] = None,
        stat_class: int = 1,
    ) -> list[dict[str, Any]]:
        """
        Fetch complete schedule for a team.

        Args:
            team_id: Team ID
            season: Season ID (default from settings)
            league_id: League ID (default from settings)
            stat_class: Stat class (default 1)

        Returns:
            List of game dictionaries

        Example return:
            [
                {
                    'game_id': 541086,
                    'team_id': 4784,
                    'date': '2024-09-10',
                    'time': '21:45',
                    'rink': 'San Jose Black (E)',
                    'league': 'SIAHL@SJ',
                    'level': 'Adult Division 1',
                    'home_team': 'Camels',
                    'away_team': 'Opponents',
                    'home_goals': 5,
                    'away_goals': 3,
                    'is_home': True,
                    'game_type': 'Regular 1',
                    'status': 'completed',  # or 'scheduled'
                    'scoresheet_url': 'https://...',
                },
                ...
            ]
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

        logger.info(f"Fetching schedule for team {team_id}, season {season}")

        try:
            html = await self._fetch_html(url, params=params)
            soup = BeautifulSoup(html, "lxml")

            # Find schedule table
            table = soup.find("table")
            if not table:
                logger.warning(f"No schedule table found for team {team_id}")
                return []

            games = self._parse_schedule_table(table, team_id=team_id)
            logger.info(f"Successfully scraped {len(games)} games for team {team_id}")
            return games

        except Exception as e:
            logger.error(f"Failed to scrape schedule for team {team_id}: {e}")
            raise

    def _parse_schedule_table(
        self,
        table: Tag,
        team_id: int,
    ) -> list[dict[str, Any]]:
        """
        Parse schedule table into game dictionaries.

        Args:
            table: BeautifulSoup table element
            team_id: Team ID for reference

        Returns:
            List of game dictionaries
        """
        games = []

        # Find all data rows (skip header)
        rows = table.find_all("tr")
        if not rows:
            return games

        # First row is header, skip it
        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) < 12:  # Need at least 12 columns based on structure
                continue

            try:
                # Extract game ID from links
                game_id = self._extract_game_id(cells)

                # Parse date and time
                date_str = cells[1].get_text(strip=True)
                time_str = cells[2].get_text(strip=True)
                parsed_date, parsed_time = self._parse_datetime(date_str, time_str)

                # Extract team names and scores
                away_team = cells[6].get_text(strip=True)
                away_goals_str = cells[7].get_text(strip=True)
                home_team = cells[8].get_text(strip=True)
                home_goals_str = cells[9].get_text(strip=True)

                # Determine if game is completed (scores present)
                away_goals = self._safe_int(away_goals_str) if away_goals_str else None
                home_goals = self._safe_int(home_goals_str) if home_goals_str else None
                status = "completed" if away_goals is not None and home_goals is not None else "scheduled"

                # Determine if current team is home or away
                # Note: We need to know the actual team name to determine this
                # For now, we'll include both and let the caller determine
                is_home = None  # Will be determined by matching team name to home/away

                # Build game data
                game_data = {
                    "game_id": game_id,
                    "team_id": team_id,
                    "date": parsed_date,
                    "time": parsed_time,
                    "rink": cells[3].get_text(strip=True),
                    "league": cells[4].get_text(strip=True),
                    "level": cells[5].get_text(strip=True),
                    "away_team": away_team,
                    "away_goals": away_goals,
                    "home_team": home_team,
                    "home_goals": home_goals,
                    "is_home": is_home,  # To be determined by caller
                    "game_type": cells[10].get_text(strip=True),
                    "status": status,
                    "scoresheet_url": self._extract_scoresheet_url(cells[11]),
                }

                games.append(game_data)
                logger.debug(
                    f"Parsed game {game_id}: {away_team} @ {home_team} on {parsed_date} at {parsed_time} ({status})"
                )

            except Exception as e:
                logger.warning(f"Failed to parse game row: {e}")
                continue

        return games

    def _extract_game_id(self, cells: list[Tag]) -> Optional[int]:
        """
        Extract game ID from table cells.

        Args:
            cells: List of table cells

        Returns:
            Game ID as integer, or None if not found
        """
        # Check Game Center column (last column, index 12)
        if len(cells) > 12:
            game_center_cell = cells[12]
        elif len(cells) > 11:
            game_center_cell = cells[11]
        else:
            return None

        # Look for links with game_id parameter
        links = game_center_cell.find_all("a")
        for link in links:
            href = link.get("href", "")
            if "game_id=" in href:
                try:
                    query_string = href.split("?", 1)[1] if "?" in href else ""
                    params = parse_qs(query_string)
                    game_id_list = params.get("game_id", [])
                    if game_id_list:
                        return int(game_id_list[0])
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to extract game ID from href '{href}': {e}")

        # Fallback: look for plain text game ID
        text = game_center_cell.get_text(strip=True)
        if text.isdigit():
            return int(text)

        return None

    def _extract_scoresheet_url(self, cell: Tag) -> Optional[str]:
        """
        Extract scoresheet URL from cell.

        Args:
            cell: Table cell containing scoresheet link

        Returns:
            Full scoresheet URL, or None if not found
        """
        link = cell.find("a")
        if link:
            href = link.get("href", "")
            if href:
                # Make absolute URL if relative
                if href.startswith("http"):
                    return href
                else:
                    return f"{self.base_url}/{href}"
        return None

    def _parse_datetime(self, date_str: str, time_str: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parse date and time strings into ISO format.

        Args:
            date_str: Date string (e.g., "Wed Sep 10", "Tue Jan 21")
            time_str: Time string (e.g., "9:45 PM")

        Returns:
            Tuple of (date in YYYY-MM-DD format, time in HH:MM format)
        """
        parsed_date = None
        parsed_time = None

        # Parse date
        try:
            # Date format: "Wed Sep 10" (no year)
            # We'll need to infer the year based on the season
            # For now, use current year or next year if month has passed
            current_year = datetime.now().year

            # Try parsing with current year
            date_with_year = f"{date_str} {current_year}"
            try:
                dt = datetime.strptime(date_with_year, "%a %b %d %Y")
                parsed_date = dt.strftime("%Y-%m-%d")
            except ValueError:
                # If parsing fails, just store the original string
                logger.warning(f"Could not parse date '{date_str}' with year {current_year}")
                parsed_date = date_str

        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            parsed_date = date_str

        # Parse time
        try:
            # Time format: "9:45 PM"
            dt = datetime.strptime(time_str, "%I:%M %p")
            parsed_time = dt.strftime("%H:%M")
        except Exception as e:
            logger.warning(f"Failed to parse time '{time_str}': {e}")
            parsed_time = time_str

        return parsed_date, parsed_time

    @staticmethod
    def _safe_int(value: str) -> Optional[int]:
        """
        Safely convert string to integer.

        Args:
            value: String value to convert

        Returns:
            Integer value, or None if conversion fails
        """
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    async def get_game_details(
        self,
        game_id: int,
    ) -> dict[str, Any]:
        """
        Fetch detailed game information from scoresheet.

        Args:
            game_id: Game ID

        Returns:
            Dictionary with game details

        Note:
            This is a placeholder for Phase 2. Will scrape:
            - Goal scorers and assists
            - Penalty details
            - Goalie stats
            - Period-by-period breakdown
        """
        url = f"{self.base_url}/oss-scoresheet"
        params = {
            "game_id": game_id,
            "mode": "display",
        }

        logger.info(f"Fetching details for game {game_id}")

        try:
            html = await self._fetch_html(url, params=params)
            # TODO: Implement detailed parsing in Phase 2
            # For now, just return basic structure
            return {
                "game_id": game_id,
                "html_content": html,  # Store for later parsing
            }

        except Exception as e:
            logger.error(f"Failed to scrape game details for {game_id}: {e}")
            raise
