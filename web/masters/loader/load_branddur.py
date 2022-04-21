from masters.tasks import load_vendorreport
import glob, os, tqdm


def load_dir(path=None, vendor="PFT"):

    for f in tqdm.tqdm(glob.glob(os.path.join(path, '*.xml'))):
        load_vendorreport.delay(f, vendor)

