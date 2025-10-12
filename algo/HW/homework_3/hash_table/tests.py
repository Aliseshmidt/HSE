from main import HashMap
import pytest


def test_hashmap_init():
    hm = HashMap()
    assert hm.capacity == 8
    assert hm.load_factor == 0.75
    assert hm.size == 0
    assert len(hm.buckets) == 8

    hm_custom = HashMap(init_cap=16, load_factor=0.5)
    assert hm_custom.capacity == 16
    assert hm_custom.load_factor == 0.5
    assert hm_custom.size == 0
    assert len(hm_custom.buckets) == 16


def test_hashmap_funcs():
    hm = HashMap()

    hm.put("key1", "value1")
    hm.put("key2", "value2")
    hm.put("key3", 123)

    assert hm.get("key1") == "value1"
    assert hm.get("key2") == "value2"
    assert hm.get("key3") == 123
    assert hm.get("nonexistent") is None

    assert len(hm) == 3

    hm.put("key1", "value1_updated")
    assert hm.get("key1") == "value1_updated"
    assert len(hm) == 3

    hm.put("key1", "value1")
    hm.put("key4", "value4")
    hm.put("key5", "value5")

    assert len(hm) == 5

    removed_value = hm.remove("key2")
    assert removed_value == "value2"
    assert len(hm) == 4
    assert hm.get("key2") is None

    removed_none = hm.remove("nonexistent")
    assert removed_none is None
    assert len(hm) == 4

    assert hm.get("key1") == "value1"
    assert hm.get("key3") == 123
    assert hm.get("key4") == "value4"
    assert hm.get("key5") == "value5"


def test_hashmap_collisions():
    hm = HashMap(init_cap=4)

    hm.put("key1", "value1")
    hm.put("key2", "value2")
    hm.put("key3", "value3")

    assert hm.get("key1") == "value1"
    assert hm.get("key2") == "value2"
    assert hm.get("key3") == "value3"

    assert len(hm) == 3