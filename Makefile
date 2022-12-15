test:
	build bitarray


clean:
	rm -f *~ rafe/*~
	rm -rf build dist
	rm -rf rafe/__pycache__ *.egg-info
	rm -rf src_cache/ work/
