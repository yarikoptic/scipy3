"""Compressed Block Sparse Row matrix format
"""

__all__ = ['bsr_matrix', 'isspmatrix_bsr']

from numpy import zeros, intc, array, asarray, arange, diff, tile, rank, \
        prod, ravel, empty, matrix, asmatrix

from sparsetools import bsr_matvec
from block import _block_matrix 
from base import isspmatrix
from sputils import isdense, upcast, isscalarlike

class bsr_matrix(_block_matrix):
    #TODO add docstring

    def __mul__(self, other): # self * other
        """ Scalar, vector, or matrix multiplication
        """
        if isscalarlike(other):
            return self._with_data(self.data * other)
        else:
            return self.dot(other)

    def matvec(self, other, output=None):
        """Sparse matrix vector product (self * other)

        'other' may be a rank 1 array of length N or a rank 2 array 
        or matrix with shape (N,1).  
        
        If the optional 'output' parameter is defined, it will
        be used to store the result.  Otherwise, a new vector
        will be allocated.
             
        """
        if isdense(other):
            M,N = self.shape
            X,Y = self.blocksize

            if other.shape != (N,) and other.shape != (N,1):
                raise ValueError, "dimension mismatch"

    
            #output array
            if output is None:
                y = empty( self.shape[0], dtype=upcast(self.dtype,other.dtype) )
            else:
                if output.shape != (M,) and output.shape != (M,1):
                    raise ValueError, "output array has improper dimensions"
                if not output.flags.c_contiguous:
                    raise ValueError, "output array must be contiguous"
                if output.dtype != upcast(self.dtype,other.dtype):
                    raise ValueError, "output array has dtype=%s "\
                            "dtype=%s is required" % \
                            (output.dtype,upcast(self.dtype,other.dtype))
                y = output
            
            
            bsr_matvec(M/X, N/Y, X, Y, \
                self.indptr, self.indices, ravel(self.data), ravel(other), y)

            if isinstance(other, matrix):
                y = asmatrix(y)

            if other.ndim == 2 and other.shape[1] == 1:
                # If 'other' was an (nx1) column vector, reshape the result
                y = y.reshape(-1,1)

            return y

        elif isspmatrix(other):
            raise TypeError, "use matmat() for sparse * sparse"

        else:
            raise TypeError, "need a dense vector"







    def transpose(self,copy=False):
        M,N = self.shape
            
        data    = self.data.swapaxes(1,2)
        indices = self.indices
        indptr  = self.indptr

        from bsc import bsc_matrix
        return bsc_matrix( (data,indices,indptr), shape=(N,M), copy=copy)
   
    def tocoo(self,copy=True):
        """Convert this matrix to COOrdinate format.

        When copy=False the data array will be shared between
        this matrix and the resultant coo_matrix.
        """
        
        M,N = self.shape
        X,Y = self.blocksize

        row  = (X * arange(M/X)).repeat(diff(self.indptr))
        row  = row.repeat(X*Y).reshape(-1,X,Y)
        row += tile( arange(X).reshape(-1,1), (1,Y) )
        row  = row.reshape(-1) 

        col  = (Y * self.indices).repeat(X*Y).reshape(-1,X,Y)
        col += tile( arange(Y), (X,1) )
        col  = col.reshape(-1)

        data = self.data.reshape(-1)

        if copy:
            data = data.copy()

        from coo import coo_matrix
        return coo_matrix( (data,(row,col)), shape=self.shape )


    def tobsc(self,blocksize=None):
        if blocksize is None:
            blocksize = self.blocksize
        elif blocksize != self.blocksize:
            return self.tocoo(copy=False).tobsc(blocksize=blocksize)

        #maintian blocksize
        X,Y = self.blocksize
        M,N = self.shape

        #use CSR->CSC to determine a permutation for BSR<->BSC
        from csr import csr_matrix
        data = arange(len(self.indices), dtype=self.indices.dtype)
        proxy = csr_matrix((data,self.indices,self.indptr),shape=(M/X,N/Y))
        proxy = proxy.tocsc()

        data    = self.data[proxy.data] #permute data
        indices = proxy.indices
        indptr  = proxy.indptr
       
        from bsc import bsc_matrix
        return bsc_matrix( (data,indices,indptr), shape=self.shape )
    
    def tobsr(self,blocksize=None,copy=False):

        if blocksize not in [None, self.blocksize]:
            return self.tocoo(copy=False).tobsr(blocksize=blocksize)
        if copy:
            return self.copy()
        else:
            return self
    
    # these functions are used by the parent class
    # to remove redudancy between bsc_matrix and bsr_matrix
    def _swap(self,x):
        """swap the members of x if this is a column-oriented matrix
        """
        return (x[0],x[1])


from sputils import _isinstance

def isspmatrix_bsr(x):
    return _isinstance(x, bsr_matrix)

