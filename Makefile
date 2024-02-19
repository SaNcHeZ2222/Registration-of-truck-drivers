all:
	python3 main.py

db_clean:
	rm -rf my_database.db
	python3 db.py

# fix:
# 	autopep8 --diff *.py