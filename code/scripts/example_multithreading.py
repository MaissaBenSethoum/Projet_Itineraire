import time
import threading


def sensor_a_worker(state, lock, stop_event):
    """
    Simule un capteur A
    """
    while not stop_event.is_set():
        data = time.time()

        with lock:
            state["sensor_a"] = data

        print(f"[A] Nouvelle donnée : {data:.3f}")
        time.sleep(0.5)


def sensor_b_worker(state, lock, stop_event):
    """
    Simule un capteur B
    """
    while not stop_event.is_set():
        data = time.time()

        with lock:
            state["sensor_b"] = data

        print(f"[B] Nouvelle donnée : {data:.3f}")
        time.sleep(0.8)


def main():
    # État partagé entre threads
    state = {
        "sensor_a": None,
        "sensor_b": None,
    }

    lock = threading.Lock()
    stop_event = threading.Event()

    # Création des threads
    thread_a = threading.Thread(
        target=sensor_a_worker,
        args=(state, lock, stop_event),
        daemon=True
    )

    thread_b = threading.Thread(
        target=sensor_b_worker,
        args=(state, lock, stop_event),
        daemon=True
    )

    print("Démarrage des threads...")

    thread_a.start()
    thread_b.start()

    try:
        while True:
            with lock:
                a = state["sensor_a"]
                b = state["sensor_b"]

            print(f"[MAIN] A={a} | B={b}")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nArrêt demandé")

    finally:
        stop_event.set()
        thread_a.join(timeout=1)
        thread_b.join(timeout=1)

        print("Fin du programme")


if __name__ == "__main__":
    main()