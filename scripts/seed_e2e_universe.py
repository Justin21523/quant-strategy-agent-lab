from __future__ import annotations

from app.core.config import Settings
from app.core.container import AppContainer

NASDAQ_HEADER = "|".join(
    [
        "Symbol",
        "Security Name",
        "Market Category",
        "Test Issue",
        "Financial Status",
        "Round Lot Size",
        "ETF",
        "NextShares",
    ]
)

OTHER_HEADER = "|".join(
    [
        "ACT Symbol",
        "Security Name",
        "Exchange",
        "CQS Symbol",
        "ETF",
        "Round Lot Size",
        "Test Issue",
        "NASDAQ Symbol",
    ]
)

NASDAQ_SAMPLE = f"""{NASDAQ_HEADER}
AAPL|Apple Inc. Common Stock|Q|N|N|100|N|N
QQQM|Invesco NASDAQ 100 ETF|G|N|N|100|Y|N
ZZZT|Test Company Common Stock|Q|Y|N|100|N|N
ABCDW|ABCD Corp Warrant|Q|N|N|100|N|N
File Creation Time: 0628202621:30|||||||
"""

EMPTY_OTHER_SAMPLE = f"{OTHER_HEADER}\n"


def main() -> None:
    settings = Settings(environment="e2e")
    container = AppContainer.build(settings)
    container.market_data_service.initialize()
    container.portfolio_service.initialize_presets()
    container.universe_service.refresh_us_common_stocks(
        nasdaq_text=NASDAQ_SAMPLE,
        other_text=EMPTY_OTHER_SAMPLE,
    )


if __name__ == "__main__":
    main()
