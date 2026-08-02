.PHONY: test demo

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

demo:
	PYTHONPATH=src python3 -m html_image_base64 sample_data --out demo_output/converted \
		--report demo_output/report.json --dashboard demo_output/dashboard.html -v
