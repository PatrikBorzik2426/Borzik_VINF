# vlastny_indexer Usage Guide

## 1. Starting the Services

From the `Borzik_VINF` dirňectory, start both indexer containers:

```bash
docker compose up --build -d
```

## 2. Accessing the Jupyter Notebook for lucene notebook implementation

1. Open your web browser and go to:  
   [http://localhost:8888](http://localhost:8888)
2. If prompted for a token, retrieve it with:
   ```bash
   docker logs vlastny_indexer
   ```
3. Open the main notebook (e.g., `lupyne_borzik.ipynb`)
4. Run the notebook that will ask you after indexing to enter search queries.

### Running Indexing and Search in the Notebook

- Run the notebook cells to perform data loading, indexing, and search queries.
- Ensure required data files (e.g., `data_games_merged_enriched_final.csv`) are present in `/workspace`.
- You can modify and execute search queries directly in the notebook cells.

## 3. Accessing vlastny_indexer for Command-Line Querying

If you want to use the command-line script (e.g., `query.py`) interactively:

1. Open a shell inside the running container:
   ```bash
   docker exec -it vlastny_indexer sh
   ```
2. Once inside, run the script:
   ```bash
   python query.py
   ```
   This will start the interactive query prompt.

## 4. Stopping the Services

To stop all containers:

```bash
docker compose down
```

---

**Notes:**
- All code and data for `vlastny_indexer` are in the `/workspace` directory inside the container, mapped from `Borzik_VINF/vlastny_indexer` on your host.
- For troubleshooting, check logs with:
  ```bash
  docker logs vlastny_indexer
  ```
