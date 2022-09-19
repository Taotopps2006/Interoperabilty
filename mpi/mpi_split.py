#!/usr/bin/env python
"""
Parallel Hello World

Running code: mpirun -np <#_of_processes> python mpi_singleP.py
                           OR
             mpirun -np <#_of_processes> python mpi_singleP.py                      
"""

from mpi4py import MPI

if __name__ == '__main__':

  comm = MPI.COMM_WORLD
  #size = MPI.COMM_WORLD.Get_size()

  size = comm.Get_size()
  rank = comm.Get_rank()
  name = MPI.Get_processor_name()

  #Determine the colour and key based on whether my rank is even.
  if rank % 2 == 0:
    subcommunicator = 'A'
    color = 0
    # Rank ordering: By default, if one don't care about the order of the processes, one can simply pass their rank in the original communicator as key, this way, the processes will retain the same order
    key = rank
  else:
    subcommunicator = 'B'
    color = 1
    key = rank
    
  # Split the global communicator
  newcomm = comm.Split(color, key)
  
  # Get my rank in the new communicator
  new_rank = newcomm.Get_rank()
  
  # Print my new rank and new communicator
  print("[MPI process %d] I am now MPI process %d in subcommunicator %c.\n" % (rank, new_rank, subcommunicator));
  
  newcomm.Free()

  #print( "Hello, World! I am process %d of %d on %s.\n" % (rank, size, name))
  #print( "Hello, World! I am process {0} of {1} on {2}.\n" .format(rank, size, name))