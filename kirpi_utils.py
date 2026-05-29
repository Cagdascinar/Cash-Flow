from datetime import date
from calendar import monthrange

def row_to_dict(r): return dict(r)
def today_str():    return date.today().isoformat()

def month_range(year, month):
    from calendar import monthrange
    _, last = monthrange(year, month)
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last:02d}"

def calc_depreciation(purchase_price, purchase_date_str, rate, method="normal"):
    today_d = date.today()
    try:
        p_date = date.fromisoformat(purchase_date_str)
    except:
        return {"book_value": purchase_price, "accumulated": 0, "annual": 0, "entries": []}
    years_used = (today_d - p_date).days / 365.25
    annual = purchase_price * rate / 100
    accumulated = min(annual * years_used, purchase_price)
    book_value   = max(purchase_price - accumulated, 0)
    entries = []
    for yr in range(1, int(years_used) + 2):
        yr_dep = min(annual, purchase_price - annual * (yr - 1))
        if yr_dep <= 0: break
        entries.append({"year": p_date.year + yr - 1, "depreciation": round(yr_dep, 2),
                        "cumulative": round(min(annual * yr, purchase_price), 2),
                        "book_value": round(max(purchase_price - min(annual * yr, purchase_price), 0), 2)})
    return {"book_value": round(book_value, 2), "accumulated": round(accumulated, 2),
            "annual": round(annual, 2), "entries": entries}
