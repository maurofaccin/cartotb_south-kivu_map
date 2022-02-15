#!/usr/bin/env python3


import gzip
import json

# import analysis_paper as analyse
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import shapely
from cartopy import feature as cfeature
from matplotlib import colors
from matplotlib.patches import Patch

plt.rcParams["font.family"] = "Fira Sans Compressed"


def plot_features(features, ax, style_f=None, **kwargs):
    """Plot the feture on the axis."""
    if isinstance(features, str):
        if features[-3:] == ".gz":
            with gzip.open(features, "rt") as fin:
                features = json.load(fin)
        else:
            with open(features, "rt") as fin:
                features = json.load(fin)

    style = {
        "facecolor": "none",
        "alpha": 0.5,
        "edgecolor": "black",
    }

    style.update(kwargs)
    for feat in features["features"]:
        if style_f is not None:
            style.update(style_f(feat["properties"]))

        try:
            shp = shapely.geometry.shape(feat["geometry"])
        except AttributeError:
            print("AttributeError")
            continue
        ax.add_geometries([shp], ccrs.PlateCarree(), **style)


def main():
    """Do the main."""
    img_crs = ccrs.PlateCarree()

    extent = [26.5, 29.5, -5.1, -1.5]
    scale = 2
    watercolor = "#84AFCC"

    plt.figure(figsize=(scale * (extent[1] - extent[0]), scale * (extent[3] - extent[2])), dpi=300)
    # Create a GeoAxes in the tile's projection.
    ax = plt.axes([0.001, 0.001, 0.999, 0.999], projection=img_crs, alpha=0)
    # Limit the extent of the map to a small longitude/latitude range.
    ax.set_extent(extent)

    # health zones
    plot_features("data/skivu_OSM_health_zones.geojson.gz", ax, alpha=0.3)

    # borders
    plot_features("data/skivu_OSM_admin0.geojson.gz", ax, linewidth=2)

    with open("data/skivu_TBIncidence.json", "rt") as fin:
        feats = json.load(fin)
    for i_f, feat in enumerate(feats["features"]):
        feat["properties"]["fill-opacity"] = 0.5 + 0.5 * i_f / len(feats["features"])
    plot_features(
        feats,
        ax,
        lambda x: {"facecolor": x["fill"], "alpha": x["fill-opacity"], "edgecolor": x["stroke"]},
    )

    plot_features("data/rivers_OSM.geojson", ax, linewidth=0.5, edgecolor=watercolor)
    plot_features("data/lakes_OSM.geojson", ax, linewidth=0, facecolor=watercolor, alpha=1)

    # plot mission location (with names)
    with open("data/mission_locations.geojson", "rt") as fin:
        missions = json.load(fin)

    for name, mission in missions.items():
        if mission["pos"] > 0 or mission["neg"] > 0:
            ax.scatter(
                [mission["center"][1]],
                [mission["center"][0]],
                s=50,
                c="black",
                alpha=1,
                zorder=10,
                transform=ccrs.PlateCarree(),
            )
            ax.text(
                mission["center"][1] + 0.03,
                mission["center"][0],
                name,
                transform=ccrs.PlateCarree(),
                fontdict={"fontfamily": "Fira Sans Compressed", "fontsize": 16},
            )

    # Use the cartopy interface to create a matplotlib transform object
    # for the Geodetic coordinate system. We will use this along with
    # matplotlib's offset_copy function to define a coordinate system which
    # translates the text by 25 pixels to the left.
    cust_aread = [
        Patch(
            edgecolor="gray",
            linewidth=1,
            # facecolor=x['properties']['fill'],
            facecolor=colors.ColorConverter.to_rgba(
                x["properties"]["fill"],
                alpha=x["properties"]["fill-opacity"],
            ),
            label=title,
        )
        for x, title in zip(feats["features"], [">0.1%", ">0.321%", ">1%"])
    ]
    cust_aread = [
        Patch(
            edgecolor="gray",
            facecolor="none",
            label="<0.1%",
            linewidth=1,
        )
    ] + cust_aread

    ax.legend(handles=cust_aread, fontsize="large", loc=2)
    plt.annotate(
        "Data by OpenStreetMap (ODbL) and Natural Earth (public domain),"
        " map produced using Cartopy",
        xy=(0.99, 0.995),
        color="#5A5A5A",
        xycoords="axes fraction",
        fontsize="x-small",
        ha="right",
        va="top",
    )

    extent2 = [10, 35, -15, 7]
    ext1 = 0.4
    ext2 = (
        ext1
        * (extent2[3] - extent2[2])
        * (extent[1] - extent[0])
        / (extent2[1] - extent2[0])
        / (extent[3] - extent[2])
    )
    ax = plt.axes(
        [0.01, 0.01, 0.01 + ext1, 0.01 + ext2],
        projection=img_crs,
        alpha=1,
        facecolor="white",
    )
    for _, sp in ax.spines.items():
        sp.set_linewidth(3)
        sp.set_edgecolor("#888888")
    ax.set_extent(extent2)

    for feat in ["admin_0_boundary_lines_land"]:
        ax.add_feature(
            cfeature.NaturalEarthFeature(
                "cultural",
                feat,
                "50m",
                facecolor="none",
                edgecolor="#777777",
                linewidth=2,
            )
        )
    for feat in ["ocean", "lakes"]:
        ax.add_feature(
            cfeature.NaturalEarthFeature(
                "physical",
                feat,
                "10m",
                facecolor=watercolor,
                edgecolor="face",
                linewidth=1,
            )
        )

    plot_features(
        "data/naturalearth_50m_rivers_lake_centerlines.geojson",
        ax,
        linewidth=1,
        facecolor="none",
        edgecolor="#557599",
    )

    plot_features(
        "data/skivu_OSM_admin0.geojson.gz",
        ax,
        linewidth=1,
        facecolor="#cc0000",
        alpha=0.75,
    )

    plt.savefig("map_figure1.pdf", dpi=100, transparent=False)


if __name__ == "__main__":
    main()
