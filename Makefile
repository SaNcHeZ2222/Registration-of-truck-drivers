all:
	python3 main.py

db_clean:
	rm -rf base.db
	python3 db.py

# fix:
# 	autopep8 --diff *.py