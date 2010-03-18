import java.util.ArrayList
from ini.trakem2.display import *
import mpicbg.trakem2.align.Align
import mpicbg.trakem2.align.AlignTask
import os

## Preferences
resetPatchPositions = True
resetLinks = True
verbose = True
reloadImages = True
hmi_folder="/home/tom/tmp/mpi/4700/small"
lmi_folder="/home/tom/tmp/mpi/2300"
nr_lmi_images = 0
nr_hmi_images = 0

## Globals
display = Display.getFront()
layer = display.getLayer()


## Helper methods
def log(message):
	if verbose == True:
		print message

def crosslink(candidates, overlapping_only=True):
	if candidates == None:
		return
	len = candidates.size()
	if len < 2:
		return
	# linking is reciprocal: need only call link()
	# on one member of the pair
	for i in range(len):
		if i + 1 == len:
			break
		for j in range(i+1, len):
			if overlapping_only == True:
				if candidates[i].intersects(candidates[j]) == False:
					continue
			candidates[i].link(candidates[j])

def load_images(path):
	# find all TIF files with filter
	#tif_files = filter(lambda x: x.endswith('.tif'), os.listdir(path))
	dir_list = [x for x in os.listdir(path) if x.endswith('.tif')]
	for f in dir_list:
		filepath = os.path.join(path, f)
		# Open the image
		imp = IJ.openImage(filepath)
		# Create a new Patch, which wraps an image
		patch = Patch(display.project, imp.title, 0, 0, imp)
		patch.project.loader.addedPatchFrom(filepath, patch)
		# Add it to a layer
		layer.add(patch)
	return len(dir_list)



def reload_images(lmi_path, hmi_path):
	global nr_lmi_images
	global nr_hmi_images
	log("reloading low-mag images from " + lmi_path)
	nr_lmi_images = load_images(lmi_path)
	log("reloading high-mag images from " + hmi_path)
	nr_hmi_images = load_images(hmi_path)
	
	
## Main part

if reloadImages == True:
	reload_images(lmi_folder, hmi_folder)

patches = layer.getDisplayables( Patch )
if patches == None:
	log("Found no patches, aborting!")

if resetPatchPositions == True:
	log("Resetting patch positions")
	for p in patches:
		p.getAffineTransform().setToIdentity()
	if verbose == True:
		display.repaint()

if resetLinks == True:
	log("Resetting patch linking")
	for p1 in patches:
		for p2 in patches:
			if p1.isLinked(p2) == True:
				p1.unlink(p2)
	

log('Dividing HMI from LMI at index')
candidate_hmis = patches.subList(0, nr_hmi_images)
candidate_lmis = patches.subList(nr_hmi_images, patches.size())

print 'Starting registration with ' + repr(candidate_lmis.size()) + ' LMI and ' + repr(candidate_hmis.size()) + ' HMI patche(s)'

working_patches = java.util.ArrayList(candidate_hmis)
dynamic_patches_idx = working_patches.size()
fixed_patches = []

# Parameterization
param = mpicbg.trakem2.align.Align.paramOptimize.clone()
param.expectedModelIndex = 1
param.desiredModelIndex = 2

# iterate over all LMI patches
for lp in candidate_lmis:
	# clear the working lists
	del fixed_patches[:]
	# the current LMI patch should be fixed
	fixed_patches.append(lp)
	
	# a working patch is every HMI and the current LMI
	working_patches = working_patches.subList(0,dynamic_patches_idx)
	working_patches.add(lp)
	
	# call the actual registration
	mpicbg.trakem2.align.AlignTask.alignPatches(param, working_patches, fixed_patches)
	
	# Link overlapping images together
	crosslink(working_patches)
	
	# TODO How do we know if an image was not aligned correctly?
	

print "Registration done"

## post processing
# resize canvas
layer.getParent().setMinimumDimensions()

# repaint everything
display.repaint()

