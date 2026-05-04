# 未実装機能ギャップ分析（v0.3.0 時点）

現在 301 ツール実装済み。以下は未実装の vSphere/vCenter API 機能一覧。

---

## 優先度: 高

### 1. VM ストレージポリシー（SPBM）— 7個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 1 | `list_storage_policies` | ストレージポリシー一覧 | REST: `GET /api/vcenter/storage/policies` |
| 2 | `get_storage_policy` | ストレージポリシー詳細（ルール含む） | REST |
| 3 | `create_storage_policy` | ストレージポリシー作成 | REST |
| 4 | `delete_storage_policy` | ストレージポリシー削除 | REST |
| 5 | `assign_storage_policy_to_vm` | VM にストレージポリシー割り当て | pyVmomi: `pbm` |
| 6 | `get_vm_storage_policy_compliance` | VM ストレージポリシー準拠状態確認 | pyVmomi: `pbm.CheckCompliance()` |
| 7 | `get_compatible_datastores` | ポリシー互換データストア検索 | pyVmomi: `pbm` |

### 2. OVF/OVA インポート・エクスポート — 5個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 8 | `export_vm_as_ovf` | VM を OVF パッケージとしてエクスポート | pyVmomi: `ExportVm()` + HttpNfcLease |
| 9 | `export_vm_as_ova` | VM を OVA としてストリームエクスポート | pyVmomi: HttpNfcLease |
| 10 | `import_ovf` | OVF/OVA を URL/データストアからインポート | pyVmomi: `ResourcePool.ImportVApp()` |
| 11 | `capture_vm_to_library` | 既存 VM をコンテンツライブラリに OVF キャプチャ | REST: `POST /api/vcenter/ovf/library-item` |
| 12 | `upload_library_item_file` | ライブラリアイテムにファイルアップロード | REST: UpdateSession |

### 3. vSAN 管理 — 9個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 13 | `get_vsan_cluster_config` | vSAN クラスタ構成取得 | pyVmomi: `vim.cluster.VsanInternalSystem` |
| 14 | `get_vsan_health_summary` | vSAN ヘルスチェックサマリー | pyVmomi: `QueryVsanStatistics()` |
| 15 | `list_vsan_disk_groups` | ホスト別ディスクグループ一覧 | pyVmomi: `vim.host.VsanSystem` |
| 16 | `add_vsan_disk_group` | ディスクグループ追加 | pyVmomi: `InitializeDisks()` |
| 17 | `remove_vsan_disk_group` | ディスクグループ削除 | pyVmomi |
| 18 | `get_vsan_resync_status` | vSAN 再同期ステータス | pyVmomi |
| 19 | `list_vsan_objects` | vSAN オブジェクト一覧（ポリシー準拠状態） | pyVmomi |
| 20 | `set_vsan_cluster_config` | vSAN 有効化/無効化・設定変更 | pyVmomi |
| 21 | `get_vsan_performance_stats` | vSAN パフォーマンス統計 | pyVmomi |

### 4. vSphere Lifecycle Manager / パッチ管理 — 8個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 22 | `list_vlcm_images` | クラスタレベル desired image 一覧 | REST: `GET /api/esx/settings/clusters/{id}/software` |
| 23 | `get_vlcm_cluster_compliance` | クラスタパッチ準拠状態 | REST |
| 24 | `apply_vlcm_image` | クラスタに desired image 適用（修復） | REST |
| 25 | `list_update_baselines` | VUM ベースライン一覧 | REST |
| 26 | `scan_host_for_patches` | ホストパッチスキャン実行 | REST |
| 27 | `remediate_host` | ホストパッチ適用（修復） | REST: `POST /api/esx/settings/hosts/{id}/software?action=apply` |
| 28 | `get_host_patch_compliance` | ホストパッチ準拠状態取得 | REST |
| 29 | `stage_patches_to_host` | ホストへパッチ事前ダウンロード | REST |

### 5. VM 暗号化 / 鍵管理 — 7個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 30 | `get_vm_encryption_state` | VM 暗号化状態取得 | pyVmomi: `vim.encryption.CryptoManager` |
| 31 | `encrypt_vm` | VM 暗号化 | pyVmomi: `Reconfigure` + `ConfigSpec.crypto` |
| 32 | `decrypt_vm` | VM 暗号化解除 | pyVmomi |
| 33 | `rekey_vm` | VM 暗号化キー再生成（shallow/deep） | pyVmomi |
| 34 | `list_key_providers` | 鍵プロバイダー一覧（Native/KMIP） | pyVmomi: `CryptoManagerKmip.ListKmipServers()` |
| 35 | `add_kmip_server` | KMIP サーバー追加 | pyVmomi |
| 36 | `set_default_key_provider` | デフォルト鍵プロバイダー設定 | pyVmomi |

---

## 優先度: 中〜高

### 6. ホストプロファイル（フルライフサイクル）— 8個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 37 | `create_host_profile` | リファレンスホストからプロファイル作成 | pyVmomi: `HostProfileManager.CreateProfile()` |
| 38 | `apply_host_profile` | ホストにプロファイル適用 | pyVmomi: `HostProfile.Apply()` |
| 39 | `export_host_profile` | ホストプロファイルエクスポート | pyVmomi |
| 40 | `import_host_profile` | ホストプロファイルインポート | pyVmomi |
| 41 | `delete_host_profile` | ホストプロファイル削除 | pyVmomi |
| 42 | `associate_host_with_profile` | ホストとプロファイル関連付け | pyVmomi |
| 43 | `remediate_host_profile` | ホストプロファイル準拠修復 | pyVmomi: `ApplyHostConfig_Task()` |
| 44 | `get_host_profile_execution_requirements` | プロファイル適用に必要なユーザー入力取得 | pyVmomi |

### 7. vCenter 証明書管理（VMCA）— 8個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 45 | `get_vcenter_certificate_info` | vCenter TLS 証明書情報取得 | REST: `GET /api/vcenter/certificate-management/vcenter/tls` |
| 46 | `renew_vcenter_certificate` | vCenter 証明書更新（VMCA） | REST |
| 47 | `replace_vcenter_certificate` | vCenter 証明書カスタム置換 | REST |
| 48 | `list_trusted_root_certs` | 信頼済みルート証明書一覧 | REST |
| 49 | `add_trusted_root_cert` | 信頼済みルート証明書追加 | REST |
| 50 | `remove_trusted_root_cert` | 信頼済みルート証明書削除 | REST |
| 51 | `replace_host_certificate` | ESXi ホスト証明書カスタム置換 | REST |
| 52 | `get_certificate_status` | 全証明書有効期限/状態一括確認 | REST |

---

## 優先度: 中

### 8. Network I/O Control（NIOC）— 5個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 53 | `get_dvs_nioc_config` | DVS NIOC 設定取得 | pyVmomi: `NetworkIoControl` |
| 54 | `enable_disable_dvs_nioc` | DVS NIOC 有効/無効 | pyVmomi |
| 55 | `list_dvs_nioc_resource_pools` | NIOC ネットワークリソースプール一覧 | pyVmomi |
| 56 | `configure_dvs_nioc_resource_pool` | NIOC リソースプール帯域設定 | pyVmomi |
| 57 | `set_vm_nioc_allocation` | VM 別ネットワーク帯域予約 | pyVmomi |

### 9. インスタントクローン — 1個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 58 | `instant_clone_vm` | 実行中 VM の瞬間フォーク | pyVmomi: `InstantClone_Task()` |

### 10. コンテンツライブラリ（拡張）— 8個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 59 | `create_subscribed_library` | サブスクライブライブラリ作成 | REST: `POST /api/content/subscribed-library` |
| 60 | `publish_library` | ローカルライブラリ公開 | REST |
| 61 | `get_library_subscription_info` | サブスクリプション設定取得 | REST |
| 62 | `update_library_subscription` | サブスクリプション設定更新 | REST |
| 63 | `sync_library_item` | 単一ライブラリアイテム同期 | REST |
| 64 | `get_library_item_download_url` | アイテムファイル一時ダウンロード URL 取得 | REST |
| 65 | `create_library_item` | 空のライブラリアイテム作成 | REST |
| 66 | `update_library_item_metadata` | アイテムメタデータ更新 | REST |

### 11. vSphere with Tanzu（Kubernetes）— 7個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 67 | `list_namespaces` | vSphere Namespace 一覧 | REST: `GET /api/vcenter/namespaces/instances` |
| 68 | `get_namespace` | Namespace 詳細（リソースクォータ含む） | REST |
| 69 | `create_namespace` | Namespace 作成 | REST |
| 70 | `delete_namespace` | Namespace 削除 | REST |
| 71 | `list_namespace_clusters` | Workload Management 有効クラスタ一覧 | REST |
| 72 | `enable_workload_management` | Tanzu 有効化 | REST |
| 73 | `get_tkgs_cluster_list` | TKGs クラスタ一覧 | REST |

### 12. スケジュールタスク（拡張）— 3個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 74 | `create_scheduled_task` | スケジュールタスク作成 | pyVmomi: `ScheduledTaskManager.CreateScheduledTask()` |
| 75 | `update_scheduled_task` | スケジュールタスク更新 | pyVmomi |
| 76 | `get_scheduled_task_detail` | スケジュールタスク詳細取得 | pyVmomi |

### 13. クロス vCenter マイグレーション — 2個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 77 | `cross_vcenter_migrate_vm` | 別 vCenter への VM マイグレーション | pyVmomi: `RelocateSpec` + `ServiceLocator` |
| 78 | `list_cross_vcenter_extension_keys` | クロス vCenter 拡張キー一覧 | pyVmomi |

### 14. PCI パススルー / SR-IOV — 5個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 79 | `list_host_pci_devices` | ホスト PCI デバイス一覧 | pyVmomi: `hostHardwareInfo` |
| 80 | `enable_pci_passthrough` | PCI パススルー有効化 | pyVmomi: `PciPassthruConfig` |
| 81 | `add_pci_passthrough_to_vm` | VM に PCI パススルーデバイス追加 | pyVmomi: `VirtualPCIPassthrough` |
| 82 | `list_host_sriov_status` | SR-IOV アダプタ状態一覧 | pyVmomi |
| 83 | `configure_host_sriov` | SR-IOV 有効化・VF 数設定 | pyVmomi |

### 15. vGPU / GPU パススルー — 4個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 84 | `list_vm_gpu_devices` | VM GPU デバイス一覧 | pyVmomi |
| 85 | `add_vgpu_to_vm` | VM に vGPU プロファイル追加 | pyVmomi: `VirtualPCIPassthrough` |
| 86 | `list_host_vgpu_profiles` | ホスト利用可能 vGPU プロファイル一覧 | pyVmomi: `GraphicsManager` |
| 87 | `get_host_gpu_status` | ホスト GPU 利用状況 | pyVmomi |

### 16. vCenter サーバー管理 — 10個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 88 | `get_vcenter_health` | vCenter ヘルス状態取得 | REST: `GET /api/vcenter/health/system` |
| 89 | `list_vcenter_services` | vCenter サービス一覧 | REST: `GET /api/vcenter/services` |
| 90 | `restart_vcenter_service` | vCenter サービス再起動 | REST |
| 91 | `get_vcenter_backup_status` | vCenter バックアップ状態取得 | REST |
| 92 | `configure_vcenter_backup` | vCenter ファイルベースバックアップ設定 | REST |
| 93 | `trigger_vcenter_backup` | vCenter オンデマンドバックアップ実行 | REST |
| 94 | `get_sso_config` | SSO/ID ソース設定取得 | REST |
| 95 | `list_identity_sources` | SSO ID ソース一覧（AD/LDAP） | REST |
| 96 | `add_identity_source` | SSO ID ソース追加 | REST |
| 97 | `list_sso_groups` | SSO グループ/メンバーシップ一覧 | REST |

---

## 優先度: 低〜中

### 17. DVS 高度な機能 — 6個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 98 | `configure_dvs_lacp` | DVS LACP 設定 | pyVmomi |
| 99 | `get_dvs_health` | DVS ヘルスチェック結果取得 | pyVmomi |
| 100 | `enable_dvs_health_check` | DVS ヘルスチェック有効/無効 | pyVmomi |
| 101 | `migrate_vm_network_to_dvs` | VM NIC 一括 DVS 移行 | pyVmomi: `RectifyDvsOnHost_Task` |
| 102 | `export_dvs_config` | DVS 設定エクスポート | pyVmomi: `ExportDvs_Task()` |
| 103 | `restore_dvs_config` | DVS 設定リストア | pyVmomi |

### 18. iSCSI 拡張設定 — 5個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 104 | `set_iscsi_chap_auth` | iSCSI CHAP 認証設定 | pyVmomi |
| 105 | `add_iscsi_static_target` | iSCSI スタティックターゲット追加 | pyVmomi |
| 106 | `remove_iscsi_target` | iSCSI ターゲット削除 | pyVmomi |
| 107 | `get_iscsi_adapter_config` | iSCSI アダプタ構成取得（IQN/CHAP/ターゲット） | pyVmomi |
| 108 | `rescan_iscsi_hba` | iSCSI HBA 再スキャン | pyVmomi |

### 19. vSphere Replication — 5個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 109 | `list_vm_replication_config` | レプリケーション構成 VM 一覧 | pyVmomi: VR 拡張 |
| 110 | `configure_vm_replication` | VM レプリケーション有効化 | pyVmomi |
| 111 | `get_replication_status` | RPO/レプリケーション健全性取得 | pyVmomi |
| 112 | `pause_resume_replication` | レプリケーション一時停止/再開 | pyVmomi |
| 113 | `test_failover` | テストリカバリ実行 | pyVmomi |

### 20. Trust Authority — 3個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 114 | `get_trust_authority_config` | Trust Authority 設定取得 | REST |
| 115 | `list_trusted_key_providers` | 信頼済みキープロバイダー一覧 | REST |
| 116 | `configure_trusted_principal` | 信頼済みプリンシパル設定 | REST |

### 21. Proactive HA / クラスタ拡張 — 3個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 117 | `get_cluster_proactive_ha_config` | Proactive HA 設定取得 | pyVmomi |
| 118 | `configure_proactive_ha` | Proactive HA 有効化/設定 | pyVmomi |
| 119 | `get_cluster_resource_usage` | クラスタ集約リソース使用率 | pyVmomi |

### 22. VM モニタリング / ゲスト拡張 — 5個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 120 | `set_vm_monitoring` | VM モニタリング設定（HA ハートビート再起動） | pyVmomi: `VmToolsMonitoringSettings` |
| 121 | `get_vm_monitoring_state` | VM モニタリング状態取得 | pyVmomi |
| 122 | `export_vm_configuration` | VM VMX 構成エクスポート | pyVmomi |
| 123 | `get_vm_uptime` | VM アップタイム計算 | pyVmomi: `runtime.bootTime` |
| 124 | `find_orphaned_vmdk` | 孤立 VMDK ファイル検出 | pyVmomi: DatastoreBrowser |

### 23. データストアファイル操作（拡張）— 2個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 125 | `get_file_download_url` | データストアファイルダウンロード URL 生成 | HTTPS datastore access |
| 126 | `upload_file_to_datastore` | データストアへファイルアップロード | HTTPS datastore access |

---

## サマリー

| 優先度 | カテゴリ数 | ツール数 |
|--------|-----------|----------|
| 高 | 5 | 36 |
| 中〜高 | 2 | 16 |
| 中 | 10 | 55 |
| 低〜中 | 6 | 19 |
| **合計** | **23** | **126** |

実装完了後の総ツール数: **301 + 126 = 427**
