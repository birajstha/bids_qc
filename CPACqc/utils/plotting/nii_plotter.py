
import nibabel as nib
import numpy as np
from nilearn.plotting import plot_stat_map

def plot_nii_overlay(in_nii, plot_loc, background=None, volume=None, cmap='viridis', title=None, alpha=0.8, threshold=20):
    im = nib.load(in_nii)
    if volume is not None:
        v = volume
        im = nib.Nifti1Image(im.get_fdata()[:,:,:,v], header=im.header, affine=im.affine)

    if threshold != 'auto':
        lb = np.percentile(np.sort(np.unique(im.get_fdata())), float(threshold))
    else:
        lb = threshold

    if background and background != 'None':
        bg = nib.load(background)
        plot_stat_map(im, bg_img=bg, output_file=plot_loc,
                      black_bg=True, threshold=lb, title=title, cmap=cmap, alpha=float(alpha))
    
    elif background == None or background == 'None':
        plot_stat_map(im, bg_img=None, output_file=plot_loc,
                      black_bg=True, threshold=lb, title=title, cmap=cmap, alpha=float(alpha))
                                                                                                        
    else:
        plot_stat_map(im, output_file=plot_loc,
                      black_bg=True, threshold=lb, title=title, cmap=cmap, alpha=float(alpha))