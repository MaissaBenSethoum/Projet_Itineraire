import argparse
import pandas as pd
import matplotlib.pyplot as plt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nuages de points du magnétomètre")
    parser.add_argument("file_path", type=str)
    parser.add_argument("-o", "--output", type=str, default="data/magneto_scatter.png")
    args = parser.parse_args()

    df = pd.read_csv(args.file_path)

    fig, axs = plt.subplots(1, 3, figsize=(15, 5))

    axs[0].scatter(df["Magneto X"], df["Magneto Y"], s=3)
    axs[0].set_xlabel("Magneto X")
    axs[0].set_ylabel("Magneto Y")
    axs[0].set_title("X / Y")
    axs[0].axis("equal")
    axs[0].grid(True)

    axs[1].scatter(df["Magneto X"], df["Magneto Z"], s=3)
    axs[1].set_xlabel("Magneto X")
    axs[1].set_ylabel("Magneto Z")
    axs[1].set_title("X / Z")
    axs[1].axis("equal")
    axs[1].grid(True)

    axs[2].scatter(df["Magneto Y"], df["Magneto Z"], s=3)
    axs[2].set_xlabel("Magneto Y")
    axs[2].set_ylabel("Magneto Z")
    axs[2].set_title("Y / Z")
    axs[2].axis("equal")
    axs[2].grid(True)

    plt.tight_layout()
    plt.savefig(args.output)
    print(f"Image sauvegardée : {args.output}")