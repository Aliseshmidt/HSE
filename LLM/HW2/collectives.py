"""Ring SUM collectives on CPU/Gloo; no input mutations or native collectives."""
import torch
import torch.distributed as dist


def _exchange(outgoing, incoming, next_rank, previous_rank):
    pending = dist.batch_isend_irecv([
        dist.P2POp(dist.isend, outgoing, next_rank),
        dist.P2POp(dist.irecv, incoming, previous_rank),
    ])
    for request in pending:
        request.wait()


def ring_reduce_scatter(tensor):
    rank, size = dist.get_rank(), dist.get_world_size()
    if tensor.ndim != 1 or tensor.numel() == 0 or tensor.numel() % size:
        raise ValueError("Expected a nonempty 1D tensor divisible by world_size")
    chunks = [part.clone().contiguous() for part in tensor.chunk(size)]
    for step in range(size - 1):
        send_index = (rank - step - 1) % size
        receive_index = (rank - step - 2) % size
        received = torch.empty_like(chunks[receive_index])
        _exchange(chunks[send_index], received, (rank + 1) % size, (rank - 1) % size)
        chunks[receive_index].add_(received)
    return chunks[rank]


def ring_all_gather(shard):
    rank, size = dist.get_rank(), dist.get_world_size()
    if shard.ndim != 1 or shard.numel() == 0:
        raise ValueError("Expected a nonempty 1D shard")
    chunks = [torch.empty_like(shard) for _ in range(size)]
    chunks[rank].copy_(shard)
    for step in range(size - 1):
        send_index = (rank - step) % size
        receive_index = (rank - step - 1) % size
        _exchange(chunks[send_index], chunks[receive_index], (rank + 1) % size, (rank - 1) % size)
    return torch.cat(chunks)


def ring_all_reduce(tensor):
    return ring_all_gather(ring_reduce_scatter(tensor))
