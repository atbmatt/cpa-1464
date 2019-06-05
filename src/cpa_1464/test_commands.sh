#!/bin/bash

python __init__.py --config "$(cat ../../tests/config.json)" | cat > ../../tests/test.txt
python __init__.py --transactions "$(cat ../../tests/test.txt)" "$(cat ../../tests/transactions.json)" | cat > ../../tests/objdump.txt
python __init__.py --generate "$(cat ../../tests/objdump.txt)" | cat > ../../tests/output.cpa1464