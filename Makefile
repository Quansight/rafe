test-build:
	rafe build bitarray
clean:
	rm -rf build dist
	rm -rf rafe/__pycache__ *.egg-info
	rm -rf src_cache/ work/
