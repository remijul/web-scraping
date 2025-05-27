import asyncio
from crawl4ai import *

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            #url="https://www.nbcnews.com/business",
            #url = "https://vivatechnology.com/get-your-pass?ca=FPR887Y6&utm_source=google&utm_medium=cpc&utm_campaign=sea_campaign_brand_FR&esl-k=GOOGLEADS|ng|c733737405817|mp|kvivatech%202025|p|t|dc|a173107040577|g22264576927&gad_source=1&gad_campaignid=22264576927&gbraid=0AAAAADMaCLbO7B4nyTklr7j1OQUMNO6Hc&gclid=Cj0KCQjwotDBBhCQARIsAG5pinNYzYtw7nydQuxoFMgh4X-Jwov0ROjXldn4UbUCmsVf1VlUutaUG4oaAvbwEALw_wcB"
            url = "https://www.lemonde.fr/"
        )
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())