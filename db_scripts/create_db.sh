rm dependency_db2.db
sqlite3 dependency_db2.db < init_db.sql
python fill_db.py dependency_db2.db arcs*
sqlite3 dependency_db2.db < create_index.sql
