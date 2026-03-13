use std

struct Point:
    let x: Int
    let y: Int


class Counter:
    let value: Int = 0

    fn inc(self, delta: Int) -> Void:
        self.value = self.value + delta


fn sum_vector(nums: Vector[Int]) -> Int:
    let total: Int = 0
    for n in nums:
        total = total + n
    return total


fn main() -> Int:
    let nums: Vector[Int] = [9, 3, 7, 1, 5]
    let sorted_nums: Vector[Int] = quick_sort(nums)

    print("sorted:", sorted_nums)
    print("index of 7:", binary_search(sorted_nums, 7))

    ptr score: Int = 10
    print("pointer value:", val(score))
    setptr score = 42
    print("updated pointer value:", val(score))

    let c: Counter = Counter()
    c.inc(8)
    print("counter:", c.value)

    print("sum:", sum_vector(sorted_nums))
    return 0


main()
