all:
	python3 main.py

clean: folder_clean
	rm -rf base.db
	rm -rf order.json
	echo "{}" > order.json
	python3 db.py
	python3 main.py

folder_clean:
	rm -rf drive
	mkdir drive
