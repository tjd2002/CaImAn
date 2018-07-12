#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 12 11:11:45 2018

@author: epnevmatikakis
"""

import numpy as np
import matplotlib.pyplot as plt
import scipy.sparse
import caiman

class Estimates(object):
    def __init__(self, A=None, b=None, C=None, f=None, dims=None):
        # variables related to the estimates of traces, footprints, deconvolution and background
        self.A = A
        self.C = C
        self.f = f
        self.b = b
        self.R = None    # formerly called YrA (residual traces)
        self.W = None
        self.b0 = None

        self.S = None
        self.sn = None
        self.g = None
        self.bl = None
        self.c1 = None
        self.neurons_sn = None
        self.lam = None

        self.center = None
        self.extra_1p = None

        self.merged_ROIs = None
        self.coordinates = None
        self.F_dff = None

        self.idx_components = None
        self.idx_components_bad = None
        self.SNR_comp = None
        self.r_values = None
        self.cnn_preds = None
        
        self.dims = dims
        
        
    def plot_contours(self, img=None, idx=None, crd=None, thr_method='max',
                      thr='0.2'):
        """view contour plots for each spatial footprint. 
        Parameters:
        -----------
        img :   np.ndarray
                background image for contour plotting. Default is the mean
                image of all spatial components (d1 x d2)
        idx :   list
                list of accepted components

        crd :   list
                list of coordinates (if empty they are computed)

        thr_method : str
                     thresholding method for computing contours ('max', 'nrg')

        thr : float
                threshold value
        """
        if 'csc_matrix' not in str(type(self.A)):
            self.A = scipy.sparse.csc_matrix(self.A)
        if img is None:
            img = np.reshape(np.array(self.A.mean(1)), self.dims, order='F')
        if not hasattr(self, 'coordinates'):
            self.coordinates = caiman.utils.visualization.get_contours(self.A, self.dims, thr=thr, thr_method=thr_method)
        plt.figure()
        if idx is None:
            caiman.utils.visualization.plot_contours(self.A, img, coordinates=self.coordinates)
        else:
            if not isinstance(idx, list):
                idx = idx.tolist()
            coor_g = [self.coordinates[cr] for cr in idx]
            bad = list(set(range(self.A.shape[1])) - set(idx))
            coor_b = [self.coordinates[cr] for cr in bad]
            plt.subplot(1, 2, 1)
            caiman.utils.visualization.plot_contours(self.A[:, idx], img,
                                                     coordinates=coor_g)
            plt.title('Accepted Components')
            bad = list(set(range(self.A.shape[1])) - set(idx))
            plt.subplot(1, 2, 2)
            caiman.utils.visualization.plot_contours(self.A[:, bad], img,
                                                     coordinates=coor_b)
            plt.title('Rejected Components')
        return self

    def view_components(self, Yr, img=None, idx=None):
        """view spatial and temporal components interactively

        Parameters:
        -----------
        Yr :    np.ndarray
                movie in format pixels (d) x frames (T)

        dims :  tuple
                dimensions of the FOV

        img :   np.ndarray
                background image for contour plotting. Default is the mean
                image of all spatial components (d1 x d2)

        idx :   list
                list of components to be plotted


        """
        if 'csc_matrix' not in str(type(self.A)):
            self.A = scipy.sparse.csc_matrix(self.A)
        if 'array' not in str(type(self.b)):
            self.b = self.b.toarray()

        plt.ion()
        nr, T = self.C.shape

        if self.R is None:
            self.compute_residuals(Yr)

        if img is None:
            img = np.reshape(np.array(self.A.mean(axis=1)), self.dims, order='F')

        if idx is None:
            caiman.utils.visualization.view_patches_bar(Yr, self.A, self.C,
                    self.b, self.f, self.dims[0], self.dims[1], YrA=self.R, img=img)
        else:
            caiman.utils.visualization.view_patches_bar(Yr, self.A.tocsc()[:,idx], 
                                                        self.C[idx], self.b, self.f, 
                                                        self.dims[0], self.dims[1], YrA=self.R[idx], img=img)

    def play_movie(self, imgs, q_max=99.75, q_min=2, gain_res=1,
                   magnification=1, include_bck=True,
                   frame_range=slice(None, None, None)):

        """Displays a movie with three panels (original data (left panel),
        reconstructed data (middle panel), residual (right panel))
        Parameters:
        -----------
        imgs: np.array (possibly memory mapped, t,x,y[,z])
            Imaging data

        q_max: float (values in [0, 100])
            percentile for maximum plotting value

        q_min: float (values in [0, 100])
            percentile for minimum plotting value

        gain_res: float
            amplification factor for residual movie

        magnification: float
            magnification factor for whole movie

        include_bck: bool
            flag for including background in original and reconstructed movie

        frame_rage: range or slice or list
            display only a subset of frames


        Returns:
        --------
        self (to stop the movie press 'q')
        """
        dims = imgs.shape[1:]
        if 'movie' not in str(type(imgs)):
            imgs = caiman.movie(imgs)
        Y_rec = self.A.dot(self.C[:, frame_range])
        Y_rec = Y_rec.reshape(dims + (-1,), order='F')
        Y_rec = Y_rec.transpose([2, 0, 1])
        #if self.params.get('init', 'nb') == -1 or self.params.get('init', 'nb') > 0:
        if self.b is not None and self.f is not None:
            B = self.b.dot(self.f[:, frame_range])
            if 'matrix' in str(type(B)):
                B = B.toarray()
            B = B.reshape(dims + (-1,), order='F').transpose([2, 0, 1])
        elif self.W is not None:
            B = self.W.dot(imgs[frame_range] - self.A.dot(self.C[:, frame_range]))
            B = B.reshape(dims + (-1,), order='F').transpose([2, 0, 1])
        else:
            B = np.zeros_like(Y_rec)
        if self.params.get('patch', 'border_pix') > 0:
            bpx = self.params.get('patch', 'border_pix')
            imgs = imgs[:, bpx:-bpx, bpx:-bpx]
            B = B[:, bpx:-bpx, bpx:-bpx]
            Y_rec = Y_rec[:, bpx:-bpx, bpx:-bpx]

        Y_res = imgs[frame_range] - Y_rec - B

        caiman.concatenate((imgs[frame_range] - (not include_bck)*B, Y_rec + include_bck*B, Y_res*gain_res), axis=2).play(q_min=q_min, q_max=q_max, magnification=magnification)

        return self
    
    def compute_residuals(self, Yr):
        """compute residual for each component (variable R)

         Parameters:
         -----------
         Yr :    np.ndarray
                 movie in format pixels (d) x frames (T)

        """
        if len(Yr.shape) > 2:
            Yr = np.reshape(Yr.transpose(1,2,0), (-1, Yr.shape[0]), order='F')
        if 'csc_matrix' not in str(type(self.A)):
            self.A = scipy.sparse.csc_matrix(self.A)
        if 'array' not in str(type(self.b)):
            self.b = self.b.toarray()
        if 'array' not in str(type(self.C)):
            self.C = self.C.toarray()
        if 'array' not in str(type(self.f)):
            self.f = self.f.toarray()

        Ab = scipy.sparse.hstack((self.A, self.b)).tocsc()
        nA2 = np.ravel(Ab.power(2).sum(axis=0))
        nA2_inv_mat = scipy.sparse.spdiags(
            1. / nA2, 0, nA2.shape[0], nA2.shape[0])
        Cf = np.vstack((self.C, self.f))
        if 'numpy.ndarray' in str(type(Yr)):
            YA = (Ab.T.dot(Yr)).T * nA2_inv_mat
        else:
            YA = caiman.mmapping.parallel_dot_product(Yr, Ab, dview=self.dview,
                        block_size=2000, transpose=True, num_blocks_per_run=5) * nA2_inv_mat

        AA = Ab.T.dot(Ab) * nA2_inv_mat
        self.R = (YA - (AA.T.dot(Cf)).T)[:, :self.A.shape[-1]].T

        return self