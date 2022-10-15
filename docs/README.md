# AzFinSim: Fintech Risk Simulation

AzFinsim is a simple Python application for synthetic risk simulation. This is forked
from https://github.com/mkiernan/azfinsim to remove all Azure infrastructure code and
simply be structured as standard Python application for risk analysis.

## Getting Started

This is a Python based application and hence requires Python 3.8 or newer to be installed
on the workstation. The application can be installed using PIP. A virtual environment is recommended
to avoid clobbering your Python environment. Alternatively, you can use the Docker-based
approach, described [here](#docker).

```sh
# clone repository
git clone https://github.com/utkarshayachit/azfinsim.git -b refactor

cd azfinsim

# create virtual environment
python3 -m venv env0

# activate virtual environment
source env0/bin/activate

# upgrade pip
python3 -m pip install --upgrade pip

# install azfinsim (-e is optional)
python3 -m pip install -e .

# validate installation
python3 -m azfinsim.azfinsim --help
# this should generate output as follows:
usage: azfinsim [-h] [--config CONFIG] [--verbose VERBOSE] ...
...

# to exit virtual environment use the following
deactivate
```

## Usage

The `azfinsim` package includes two applications, `azfinsim` and `generator`.
`azfinsim` processes trades from a redis cache, and the `generator` can be used to
populate the redis cache with synthetic trades.

To populate the cache, use the following command (within the virtual environment,
if applicable).

```sh
# activate virtual env, if not already
source env0/bin/activate

# generate trades
python3 -m azfinsim.generator --cache-name <redis url>      \
        --cache-key <redis key>                             \
        --start-trade <start trade number>                  \
        --trade-window <total number of trades to generate>
```

Once the database has been populated, you can process the trades using the following
command:

```sh
# process trades
python3 -m azfinsim.azfinsim --cache-name <redis url>       \
        --cache-key <redis key>                             \
        --start-trade <start trade number>                  \
        --trade-window <total number of trades to process>
```

Optionally, arguments can be read in from a json config file which can be specified
using the `--config` command line option.

## Docker

Instead of installing the application locally, you can build and use a
container instead. For that, you'll need Docker installed on your workstation.

```sh
# clone repository
git clone https://github.com/utkarshayachit/azfinsim.git -b refactor

cd azfinsim
# to build the container image
docker build -t azfinsim:latest .

# test the container
docker run -it azfinsim:latest -m azfinsim.azfinsim --help

# now, you can run the application using the following instead of
# `python3` (as described earlier)

# generate trades
docker run -it azfinsim:latest -m azfinsim.generator        \
        --cache-name <redis url>                            \
        --cache-key <redis key>                             \
        --start-trade <start trade number>                  \
        --trade-window <total number of trades to generate>

# process trades
docker run -it azfinsim:latest -m azfinsim.azfinsim         \
        --cache-name <redis url>                            \
        --cache-key <redis key>                             \
        --start-trade <start trade number>                  \
        --trade-window <total number of trades to process>
```
