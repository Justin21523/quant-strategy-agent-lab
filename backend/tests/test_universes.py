from app.services.universe_service import parse_nasdaq_listed, parse_other_listed
from fastapi.testclient import TestClient

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

OTHER_SAMPLE = f"""{OTHER_HEADER}
IBM|International Business Machines Corporation Common Stock|N|IBM|N|100|N|IBM
SPY|SPDR S&P 500 ETF Trust|P|SPY|Y|100|N|SPY
TST|Test Issue Common Stock|A|TST|N|100|Y|TST
"""


def test_symbol_directory_parser_filters_to_common_stocks() -> None:
    nasdaq = parse_nasdaq_listed(NASDAQ_SAMPLE)
    other = parse_other_listed(OTHER_SAMPLE)

    assert [item.symbol for item in nasdaq] == ["AAPL"]
    assert [item.symbol for item in other] == ["IBM"]
    assert other[0].exchange == "NYSE"


def test_universe_refresh_and_read_from_repository(client: TestClient) -> None:
    service = client.app.state.container.universe_service

    result = service.refresh_us_common_stocks(
        nasdaq_text=NASDAQ_SAMPLE,
        other_text=OTHER_SAMPLE,
    )

    assert result.summary.universe_id == "us_common_stocks"
    assert [member.symbol for member in result.members] == ["AAPL", "IBM"]

    response = client.get("/api/v1/universes/us_common_stocks")
    assert response.status_code == 200
    body = response.json()
    assert body["universe"]["member_count"] == 2
    assert [member["symbol"] for member in body["members"]] == ["AAPL", "IBM"]
