# Реализуйте собственную хеш-таблицу — структуру данных, которая хранит пары «ключ–значение» и позволяет выполнять три операции:
#  • вставка элемента,
#  • поиск по ключу,
#  • удаление элемента.
#
# Важно! Задание полностью творческое, чем больше аспектов будет учтено в реализации, тем лучше.
#
# На что стоит обратить внимание:
#  • Как хранить данные?
#  • Как разрешать коллизии?
#  • Что делать, если таблица заполнится?
#
# Важно! Для хранения значений можно использовать только list!

class HashMap:
    def __init__(self, init_cap=8, load_factor=0.75):
        self.capacity = init_cap
        self.load_factor = load_factor
        self.size = 0
        self.buckets = [[] for _ in range(self.capacity)]

    def _hash(self, key):
        return hash(key) % self.capacity

    def put(self, key, value):
        if self._should_resize():
            self._resize()

        index = self._hash(key)
        bucket = self.buckets[index]

        for i, (k, v) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return

        bucket.append((key, value))
        self.size += 1

    def get(self, key):
        index = self._hash(key)
        bucket = self.buckets[index]

        for k, v in bucket:
            if k == key:
                return v

        return None

    def remove(self, key):
        index = self._hash(key)
        bucket = self.buckets[index]

        for i, (k, v) in enumerate(bucket):
            if k == key:
                del bucket[i]
                self.size -= 1
                return v

        return None

    def _should_resize(self):
        current_load = self.size / self.capacity
        return current_load > self.load_factor

    def _resize(self):
        old_buckets = self.buckets

        self.capacity *= 2
        self.size = 0
        self.buckets = [[] for _ in range(self.capacity)]

        for bucket in old_buckets:
            for key, value in bucket:
                self.put(key, value)

    def __contains__(self, key):
        return self.get(key) is not None

    def __len__(self):
        return self.size

    def keys(self):
        result = []
        for bucket in self.buckets:
            for key, value in bucket:
                result.append(key)
        return result

    def values(self):
        result = []
        for bucket in self.buckets:
            for key, value in bucket:
                result.append(value)
        return result

    def items(self):
        result = []
        for bucket in self.buckets:
            for item in bucket:
                result.append(item)
        return result

