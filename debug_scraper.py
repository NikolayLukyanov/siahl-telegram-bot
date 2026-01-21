"""Debug script to test team scraper."""
import asyncio
from bs4 import BeautifulSoup
from src.services.scraper.team_scraper import TeamScraper
from src.config import settings

async def main():
    print(f"Testing TeamScraper...")
    print(f"League ID: {settings.default_league_id}")
    print(f"Season: {settings.current_season}")
    print(f"Base URL: {settings.siahl_base_url}")
    print("-" * 50)

    scraper = TeamScraper()

    try:
        # Fetch the HTML
        url = f"{scraper.base_url}/display-stats.php"
        params = {"league": settings.default_league_id}

        print(f"\nFetching: {url}?league={params['league']}")
        html = await scraper._fetch_html(url, params=params)

        print(f"HTML length: {len(html)} bytes")

        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, "lxml")

        # Check for h1/h2 tags
        h1_tags = soup.find_all("h1")
        h2_tags = soup.find_all("h2")
        h3_tags = soup.find_all("h3")

        print(f"\nFound {len(h1_tags)} h1 tags")
        print(f"Found {len(h2_tags)} h2 tags")
        print(f"Found {len(h3_tags)} h3 tags")

        if h1_tags:
            print("\nFirst h1:", h1_tags[0].get_text(strip=True)[:100])
        if h2_tags:
            print("First h2:", h2_tags[0].get_text(strip=True)[:100])
        if h3_tags:
            print("First h3:", h3_tags[0].get_text(strip=True)[:100])

        # Find all tables
        tables = soup.find_all("table")
        print(f"\nFound {len(tables)} table tags")

        # Look for division text
        print("\nSearching for 'Division' text...")
        all_text = soup.get_text()
        if "Adult Division" in all_text:
            print("✓ Found 'Adult Division' in page text")
            # Find elements containing "Adult Division"
            for tag in soup.find_all(string=lambda text: text and "Adult Division" in text):
                parent = tag.parent
                print(f"  Parent tag: <{parent.name}> - Text: {tag.strip()[:50]}")
        else:
            print("✗ 'Adult Division' NOT found in page")

        # Try the actual scraper
        print("\n" + "=" * 50)
        print("Running actual scraper...")
        teams = await scraper.get_all_teams()
        print(f"\nResult: Found {len(teams)} teams")

        if teams:
            print("\nFirst 3 teams:")
            for team in teams[:3]:
                print(f"  {team['name']} ({team['division']}) - {team['wins']}-{team['losses']}")
        else:
            print("No teams returned!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
