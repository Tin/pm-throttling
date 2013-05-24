#!/bin/sh
echo "3 workers"
python example_worker.py;python example_worker.py;python example_worker.py
echo "done!"