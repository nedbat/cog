# Create .pth files for provided modules in the current Python installation
import os, path, sys
sitepackages = path.path(sys.prefix) / 'Lib' / 'site-packages'
curdir = path.path(os.getcwd())
for module in sys.argv[1:]:
    pth = sitepackages / (module + '.pth')
    moddir = curdir / module
    print "Creating %s pointing to %s" % (pth, moddir)
    pth.write_text(moddir.abspath())
