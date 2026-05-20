import pandas as pd

df = pd.read_csv("data/test_magneto_calibration.csv")

for axe in ["Magneto X","Magneto Y","Magneto Z"]:

    minv = df[axe].min()
    maxv = df[axe].max()

    offset=(maxv+minv)/2

    print(
        f"{axe}: "
        f"min={minv:.3f} "
        f"max={maxv:.3f} "
        f"offset={offset:.3f}"
    )