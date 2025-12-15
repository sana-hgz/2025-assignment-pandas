"""Plotting referendum results in pandas.

In short, we want to make beautiful map to report results of a referendum. In
some way, we would like to depict results with something similar to the maps
that you can find here:
https://github.com/x-datascience-datacamp/datacamp-assignment-pandas/blob/main/example_map.png

To do that, you will load the data as pandas.DataFrame, merge the info and
aggregate them by regions and finally plot them on a map using `geopandas`.
"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


def load_data():
    """Load data from the CSV files referendum/regions/departments.

    Reads the CSV files from the `data/` folder and returns three
    pandas.DataFrame objects: referendum, regions, departments.
    """
    referendum = pd.read_csv('data/referendum.csv', sep=';')
    regions = pd.read_csv('data/regions.csv')
    departments = pd.read_csv('data/departments.csv')

    return referendum, regions, departments


def merge_regions_and_departments(regions, departments):
    """Merge regions and departments in one DataFrame.

    The input DataFrames are the raw CSV reads. Regions uses columns
    `code` and `name` while departments uses `region_code`, `code` and
    `name`. We merge on `regions.code == departments.region_code` and
    return the four columns renamed to the expected names.

    The columns in the final DataFrame should be:
    ['code_reg', 'name_reg', 'code_dep', 'name_dep']
    """
    merged = pd.merge(
        regions,
        departments,
        left_on='code',
        right_on='region_code',
        how='inner'
    )
    regions_and_departments = merged[[
        'code_x', 'name_x', 'code_y', 'name_y'
    ]].rename(columns={
        'code_x': 'code_reg',
        'name_x': 'name_reg',
        'code_y': 'code_dep',
        'name_y': 'name_dep'
    })
    return regions_and_departments


def merge_referendum_and_areas(referendum, regions_and_departments):
    """Merge referendum and regions_and_departments in one DataFrame.

    You can drop the lines relative to DOM-TOM-COM departments, and the
    french living abroad, which all have a code that contains `Z`.

    DOM-TOM-COM departments are departements that are remote from metropolitan
    France, like Guadaloupe, Reunion, or Tahiti.
    """
    # Normalize department codes in the referendum table so they match the
    # `code_dep` values coming from the departments CSV (e.g. '1' -> '01').
    ref = referendum.copy()
    ref['code_dep'] = ref['Department code'].astype(str).str.zfill(2)

    referendum_and_areas = pd.merge(
        ref,
        regions_and_departments,
        left_on='code_dep',
        right_on='code_dep',
        how='inner'
    )
    referendum_and_areas = referendum_and_areas[
        ~referendum_and_areas['code_dep'].str.contains('Z')
    ]
    return referendum_and_areas


def compute_referendum_result_by_regions(referendum_and_areas):
    """Return a table with the absolute count for each region.

    The return DataFrame should be indexed by `code_reg` and have columns:
    ['name_reg', 'Registered', 'Abstentions', 'Null', 'Choice A', 'Choice B']
    """
    result = referendum_and_areas.groupby('code_reg').agg({
        'name_reg': 'first',
        'Registered': 'sum',
        'Abstentions': 'sum',
        'Null': 'sum',
        'Choice A': 'sum',
        'Choice B': 'sum'
    })
    return result


def plot_referendum_map(referendum_result_by_regions):
    """Plot a map with the results from the referendum.

    * Load the geographic data with geopandas from `regions.geojson`.
    * Merge these info into `referendum_result_by_regions`.
    * Use the method `GeoDataFrame.plot` to display the result map. The results
      should display the rate of 'Choice A' over all expressed ballots.
    * Return a gpd.GeoDataFrame with a column 'ratio' containing the results.
    """
    gdf = gpd.read_file('data/regions.geojson')

    # Ensure keys are strings for consistent merging
    gdf['code'] = gdf['code'].astype(str)
    # referendum_result_by_regions is indexed by code_reg (strings like '01')
    referendum_result_by_regions = referendum_result_by_regions.copy()
    idx = referendum_result_by_regions.index.astype(str)
    referendum_result_by_regions.index = idx

    # Merge on the geojson 'code' column
    gdf = gdf.merge(
        referendum_result_by_regions,
        left_on='code',
        right_index=True,
        how='left'
    )

    # Compute ratio safely (avoid division by zero)
    expressed = gdf['Choice A'].fillna(0) + gdf['Choice B'].fillna(0)
    gdf['ratio'] = gdf['Choice A'].fillna(0) / expressed.replace({0: pd.NA})

    gdf.plot(column='ratio', legend=True, figsize=(12, 10))
    return gdf


if __name__ == "__main__":

    referendum, df_reg, df_dep = load_data()
    regions_and_departments = merge_regions_and_departments(
        df_reg, df_dep
    )
    referendum_and_areas = merge_referendum_and_areas(
        referendum, regions_and_departments
    )
    referendum_results = compute_referendum_result_by_regions(
        referendum_and_areas
    )
    print(referendum_results)

    plot_referendum_map(referendum_results)
    plt.show()
