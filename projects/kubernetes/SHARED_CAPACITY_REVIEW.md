# DRA shared consumable capacity review

[Kubernetes PR #140084](https://github.com/kubernetes/kubernetes/pull/140084) merged on November 16, 2026.
These examples compare the [base and reviewed head](https://github.com/kubernetes/kubernetes/compare/44029f5ffb0b08e5b587b33545b28e1a0c79add1...ced89708bbfbf07c69eb4c461873c8f8e3d82fc6).
They illustrate how to check a review claim against code. Use the applicable
checkout and API contract for later changes.

- **Compatibility and admission.** The old device requirement used a quantity
  value. The final API keeps the shared budget as a value and gives the
  requirement a pointer so that explicit zero and an absent union member can
  be distinguished. On a fresh write with the gate off, dropping a lone
  `valueFrom` leaves an invalid empty union. The strategy tests pass the
  prepared object through REST validation across served versions and include
  updates of stored objects and repairs. [Compatibility discussion](https://github.com/kubernetes/kubernetes/pull/140084#discussion_r3616851461),
  [base type](https://github.com/kubernetes/kubernetes/blob/44029f5ffb0b08e5b587b33545b28e1a0c79add1/staging/src/k8s.io/api/resource/v1/types.go#L717-L724), [final types](https://github.com/kubernetes/kubernetes/blob/ced89708bbfbf07c69eb4c461873c8f8e3d82fc6/staging/src/k8s.io/api/resource/v1/types.go#L718-L764),
  [strategy tests](https://github.com/kubernetes/kubernetes/blob/ced89708bbfbf07c69eb4c461873c8f8e3d82fc6/pkg/registry/resource/resourceslice/strategy_test.go#L1510-L1627).
- **Reconstructing usage.** An early review explored storing fixed costs on
  every share. The final API charges current fixed costs once per physical
  device with non-admin use and saves request-dependent amounts separately
  for each allocation. With no saved amount, request-dependent use counts as
  zero. The scheduler input retains known snapshots, including zero values.
  The earlier proposal for an `Incomplete` flag was superseded.
  [Design discussion](https://github.com/kubernetes/kubernetes/pull/140084#discussion_r3631820999), [scheduler input discussion](https://github.com/kubernetes/kubernetes/pull/140084#discussion_r4495294125),
  [allocation result](https://github.com/kubernetes/kubernetes/blob/ced89708bbfbf07c69eb4c461873c8f8e3d82fc6/staging/src/k8s.io/api/resource/v1/types.go#L2459-L2513), [scheduler input](https://github.com/kubernetes/kubernetes/blob/ced89708bbfbf07c69eb4c461873c8f8e3d82fc6/staging/src/k8s.io/dynamic-resource-allocation/structured/schedulerapi/types.go#L90-L115).
- **Pending-to-persisted handoff.** During PreBind, a persisted share can
  still appear in the pending set. After the rebase, the scheduler fed the same
  filtered allocation to capacity accounting and counter tracking so that
  suppressing a duplicate share did not also discard its saved counters.
  The regression test checks allocated capacity of two and counter consumption
  of three before persistence, during overlap and after pending cleanup.
  [Final review](https://github.com/kubernetes/kubernetes/pull/140084#pullrequestreview-5926117471), [scheduler](https://github.com/kubernetes/kubernetes/blob/ced89708bbfbf07c69eb4c461873c8f8e3d82fc6/pkg/scheduler/framework/plugins/dynamicresources/dra_manager.go#L423-L479),
  [handoff assertions](https://github.com/kubernetes/kubernetes/blob/ced89708bbfbf07c69eb4c461873c8f8e3d82fc6/pkg/scheduler/framework/plugins/dynamicresources/dynamicresources_test.go#L1418-L1447).
- **Reservation and rollback.** An author reply described a private key for
  exclusive admin reservations. A reviewer confirmed the backtracking test
  passed on that intermediate commit. At the final head,
  an admin request checks the total and reserves no counters. Trace the
  mutations an attempt actually makes before designing its inverse.
  [Intermediate confirmation](https://github.com/kubernetes/kubernetes/pull/140084#discussion_r4563507914), [final allocation path](https://github.com/kubernetes/kubernetes/blob/ced89708bbfbf07c69eb4c461873c8f8e3d82fc6/staging/src/k8s.io/dynamic-resource-allocation/structured/internal/experimental/allocator_experimental.go#L1669-L1700).
- **Error precedence.** Both the base and the head defer a missing-capacity
  rejection until ordinary name conflicts have been checked. The head also
  handles names used only by a counter. In counter resolution, a policy
  rejection leaves the loop running so a later arithmetic error can surface.
  The feature reuses an existing error contract and extends it to new inputs.
  [Alias discussion](https://github.com/kubernetes/kubernetes/pull/140084#discussion_r4495945337), [base resolver](https://github.com/kubernetes/kubernetes/blob/44029f5ffb0b08e5b587b33545b28e1a0c79add1/staging/src/k8s.io/dynamic-resource-allocation/structured/internal/experimental/consumable_capacity.go#L176-L212),
  [head resolver](https://github.com/kubernetes/kubernetes/blob/ced89708bbfbf07c69eb4c461873c8f8e3d82fc6/staging/src/k8s.io/dynamic-resource-allocation/structured/internal/experimental/consumable_capacity.go#L176-L216), [counter resolution](https://github.com/kubernetes/kubernetes/blob/ced89708bbfbf07c69eb4c461873c8f8e3d82fc6/staging/src/k8s.io/dynamic-resource-allocation/structured/internal/experimental/allocator_experimental.go#L1939-L1963).
- **Copy semantics.** A reviewer requested a defensive copy of a counter
  before subtraction, and the controller retained the call. In the reviewed
  apimachinery revision, `Quantity` already has independent value copies
  and `DeepCopy` returns the receiver. The call's presence alone cannot
  establish that a shallow copy would corrupt informer data on this revision.
  [Review and reply](https://github.com/kubernetes/kubernetes/pull/140084#discussion_r4583262699), [controller](https://github.com/kubernetes/kubernetes/blob/ced89708bbfbf07c69eb4c461873c8f8e3d82fc6/pkg/controller/resourcepoolstatusrequest/views.go#L383-L400),
  [quantity implementation](https://github.com/kubernetes/kubernetes/blob/ced89708bbfbf07c69eb4c461873c8f8e3d82fc6/staging/src/k8s.io/apimachinery/pkg/api/resource/quantity.go#L657-L664).
- **What the tests prove.** In the scheduler integration suite, a bound pod can
  still be Pending. The release test keeps a competing device available,
  checks that its pod stays unbound while a share survives, then observes
  binding after the final release. In unit tests, results include the new
  field in the normal expectation, so an unexpected snapshot can fail a test.
  [Scheduling concern](https://github.com/kubernetes/kubernetes/pull/140084#discussion_r4249435864), [release test](https://github.com/kubernetes/kubernetes/blob/ced89708bbfbf07c69eb4c461873c8f8e3d82fc6/test/integration/dra/shared_consumable_capacity.go#L278-L340),
  [result comparison discussion](https://github.com/kubernetes/kubernetes/pull/140084#discussion_r4578166061), [allocator harness](https://github.com/kubernetes/kubernetes/blob/ced89708bbfbf07c69eb4c461873c8f8e3d82fc6/staging/src/k8s.io/dynamic-resource-allocation/structured/internal/allocatortesting/allocator_testing.go#L11389-L11419).
- **Performance follow-up.** The final allocator reconstructs fixed usage from
  pool slices. When initializing a pool's budget it iterates the saved snapshot
  map and filters by driver and pool. An earlier reply described an allocated-device
  index. The final review accepted the scan for alpha and left indexing as a
  performance question for beta. [Earlier reply](https://github.com/kubernetes/kubernetes/pull/140084#discussion_r4506241170),
  [final discussion](https://github.com/kubernetes/kubernetes/pull/140084#discussion_r4583262709), [allocator](https://github.com/kubernetes/kubernetes/blob/ced89708bbfbf07c69eb4c461873c8f8e3d82fc6/staging/src/k8s.io/dynamic-resource-allocation/structured/internal/experimental/allocator_experimental.go#L1984-L2075).
