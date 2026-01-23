from typing import Any

#%% Introduce helper functions to handle both gdf rows from itertuple and iterrows loops 
# Switched to itertuple loop for computational efficiency

# equivalent to - gdf_row.get("id")
def row_get(row: Any, 
            key: str, 
            default = None):
    if hasattr(row, "_fields"):  # itertuples namedtuple
        return getattr(row, key, default)
    else:  # pd.Series
        return row.get(key, default)

# equivalent to - gdf_row.items()
def row_items(row: Any):
    if hasattr(row, "_fields"):
        return zip(row._fields, row)
    else:
        return row.items()

# equivalent to - "item" in gdf_row
def row_has(row: Any, key: str) -> bool:
    if hasattr(row, "_fields"):
        return hasattr(row, key)
    else:
        return key in row