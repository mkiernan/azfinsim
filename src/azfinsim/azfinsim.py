from .details import getargs, azfinsim

args = getargs.getargs("azfinsim")
azfinsim.execute(args)
