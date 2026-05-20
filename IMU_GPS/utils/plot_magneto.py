import argparse
import pandas as pd
import matplotlib.pyplot as plt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trace les données du magnétomètre")
    parser.add_argument("file_path", type=str, help="CSV d'acquisition")
    parser.add_argument("-o", "--output", type=str, default=None, help="Image de sortie")
    args = parser.parse_args()

    df = pd.read_csv(args.file_path)

    plt.figure()
    plt.plot(df["Timestamp"], df["Magneto X"], label="Magneto X")
    plt.plot(df["Timestamp"], df["Magneto Y"], label="Magneto Y")
    plt.plot(df["Timestamp"], df["Magneto Z"], label="Magneto Z")

    plt.xlabel("Timestamp")
    plt.ylabel("Champ magnétique (gauss)")
    plt.title("Évolution du magnétomètre")
    plt.legend()
    plt.grid(True)

    if args.output:
        plt.savefig(args.output)
        print(f"Image sauvegardée : {args.output}")
    else:
        plt.show()