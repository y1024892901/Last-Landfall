using System;
using UnityEngine;

namespace LastLandfall.Prototype
{
    /// <summary>
    /// Autonomous survivor/resident character behavior for Last Landfall.
    /// Handles procedural walking motion, idle animation, task assignment, and settlement patrol.
    /// </summary>
    [SelectionBase]
    public sealed class SurvivorCharacterController : MonoBehaviour
    {
        [Header("Identity & Role")]
        [SerializeField] private string residentName = "幸存者";
        [SerializeField] private string profession = "搜救员";
        [SerializeField] private float healthPercent = 100f;
        [SerializeField] private float moralePercent = 85f;

        [Header("Locomotion")]
        [SerializeField] private float walkSpeed = 1.4f;
        [SerializeField] private float wanderRadius = 6.0f;
        [SerializeField] private float idleDurationMin = 3.0f;
        [SerializeField] private float idleDurationMax = 7.0f;

        private Vector3 spawnOrigin;
        private Vector3 currentTarget;
        private bool isWalking;
        private float nextStateTimer;
        private float stepCycle;
        private Transform leftLeg;
        private Transform rightLeg;
        private Transform leftArm;
        private Transform rightArm;
        private Transform head;
        private Quaternion leftLegRest, rightLegRest, leftArmRest, rightArmRest, headRest;
        private IslandConstructionGrid terrainGrid;
        private IslandGrassCover grassCover;

        public string ResidentName => residentName;
        public string Profession => profession;
        public float HealthPercent => healthPercent;
        public float MoralePercent => moralePercent;
        public bool IsWalking => isWalking;

        private void Awake()
        {
            spawnOrigin = transform.position;
            currentTarget = spawnOrigin;
            nextStateTimer = UnityEngine.Random.Range(idleDurationMin, idleDurationMax);

            // Imported FBX roots differ between Unity versions; find the actual
            // hip and shoulder pivots, with the whole limb parented beneath each.
            leftLeg = FindJoint("UpperLeg_Left"); rightLeg = FindJoint("UpperLeg_Right");
            leftArm = FindJoint("UpperArm_Left"); rightArm = FindJoint("UpperArm_Right");
            head = FindJoint("Head");
            leftLegRest = leftLeg != null ? leftLeg.localRotation : Quaternion.identity;
            rightLegRest = rightLeg != null ? rightLeg.localRotation : Quaternion.identity;
            leftArmRest = leftArm != null ? leftArm.localRotation : Quaternion.identity;
            rightArmRest = rightArm != null ? rightArm.localRotation : Quaternion.identity;
            headRest = head != null ? head.localRotation : Quaternion.identity;
            var prototype = FindAnyObjectByType<BuildPlacementPrototype>();
            terrainGrid = prototype != null ? prototype.ConstructionGrid : null;
            grassCover = prototype != null ? prototype.GetComponent<IslandGrassCover>() : null;
        }

        private Transform FindJoint(string jointName)
        {
            foreach (Transform child in GetComponentsInChildren<Transform>(true))
                if (string.Equals(child.name, jointName, StringComparison.Ordinal)) return child;
            return null;
        }

        private bool TryGround(Vector3 worldPosition, out Vector3 ground)
        {
            ground = worldPosition;
            if (terrainGrid == null) return true;
            Vector3 local = terrainGrid.Root.InverseTransformPoint(worldPosition);
            if (!terrainGrid.TrySample(local.x, local.z, out Vector3 point, out Vector3 normal) || normal.y < .78f ||
                (grassCover != null && grassCover.IsFreshWater(point)))
                return false;
            ground = terrainGrid.Root.TransformPoint(point);
            return true;
        }

        private void Update()
        {
            if (isWalking)
            {
                Vector3 toTarget = currentTarget - transform.position;
                toTarget.y = 0f;

                if (toTarget.magnitude > 0.15f)
                {
                    Vector3 moveDir = toTarget.normalized;
                    Vector3 next = transform.position + moveDir * (walkSpeed * Time.deltaTime);
                    if (!TryGround(next, out Vector3 ground))
                    {
                        isWalking = false;
                        nextStateTimer = UnityEngine.Random.Range(idleDurationMin, idleDurationMax);
                        ResetLimbs();
                        return;
                    }
                    transform.position = ground;

                    // Face move direction smoothly
                    Quaternion targetRot = Quaternion.LookRotation(moveDir, Vector3.up);
                    transform.rotation = Quaternion.Slerp(transform.rotation, targetRot, 8f * Time.deltaTime);

                    // Procedural walk animation
                    stepCycle += Time.deltaTime * walkSpeed * 6.0f;
                    float legSwing = Mathf.Sin(stepCycle) * 25f;
                    float armSwing = -Mathf.Sin(stepCycle) * 22f;
                    float verticalBob = Mathf.Abs(Mathf.Sin(stepCycle)) * 0.04f;

                    if (leftLeg != null) leftLeg.localRotation = leftLegRest * Quaternion.Euler(legSwing, 0f, 0f);
                    if (rightLeg != null) rightLeg.localRotation = rightLegRest * Quaternion.Euler(-legSwing, 0f, 0f);
                    if (leftArm != null) leftArm.localRotation = leftArmRest * Quaternion.Euler(armSwing, 0f, 0f);
                    if (rightArm != null) rightArm.localRotation = rightArmRest * Quaternion.Euler(-armSwing, 0f, 0f);

                    Vector3 pos = transform.position;
                    // Maintain ground alignment
                    transform.position = new Vector3(pos.x, ground.y + verticalBob, pos.z);
                }
                else
                {
                    isWalking = false;
                    nextStateTimer = UnityEngine.Random.Range(idleDurationMin, idleDurationMax);
                    ResetLimbs();
                }
            }
            else
            {
                // Idle breathing & subtle head turn
                nextStateTimer -= Time.deltaTime;
                float breath = Mathf.Sin(Time.time * 2.2f) * 0.015f;
                Vector3 idlePosition = transform.position;
                if (TryGround(idlePosition, out Vector3 idleGround))
                    transform.position = new Vector3(idlePosition.x, idleGround.y + breath, idlePosition.z);

                if (head != null)
                {
                    float headTurn = Mathf.Sin(Time.time * 0.8f) * 12f;
                    head.localRotation = headRest * Quaternion.Euler(0f, headTurn, 0f);
                }

                if (nextStateTimer <= 0f)
                {
                    PickNewDestination();
                }
            }
        }

        private void ResetLimbs()
        {
            if (leftLeg != null) leftLeg.localRotation = leftLegRest;
            if (rightLeg != null) rightLeg.localRotation = rightLegRest;
            if (leftArm != null) leftArm.localRotation = leftArmRest;
            if (rightArm != null) rightArm.localRotation = rightArmRest;
        }

        private void PickNewDestination()
        {
            for (int attempt = 0; attempt < 12; attempt++)
            {
                Vector2 randomCircle = UnityEngine.Random.insideUnitCircle * wanderRadius;
                Vector3 candidate = new Vector3(spawnOrigin.x + randomCircle.x, spawnOrigin.y, spawnOrigin.z + randomCircle.y);
                if (!TryGround(candidate, out Vector3 ground)) continue;
                currentTarget = ground;
                isWalking = true;
                return;
            }
            nextStateTimer = UnityEngine.Random.Range(idleDurationMin, idleDurationMax);
        }

        public void SetProfile(string name, string job)
        {
            residentName = name;
            profession = job;
        }

        public void SetSpawnPoint(Vector3 position)
        {
            if (TryGround(position, out Vector3 ground)) position = ground;
            spawnOrigin = position;
            transform.position = position;
            currentTarget = position;
        }

        /// <summary>
        /// Factory method to spawn a stylized survivor character in the settlement.
        /// </summary>
        public static SurvivorCharacterController Spawn(Vector3 worldPosition, string name, string job, Transform parent = null)
        {
            bool technician = !string.IsNullOrEmpty(job) && (job.Contains("技术") || job.Contains("维修"));
            string variant = technician ? "Survivor_Technician_v2" : "Survivor_Rescuer_v2";
            GameObject prefab = Resources.Load<GameObject>("Models/Characters/" + variant) ??
                Resources.Load<GameObject>("Models/Characters/Survivor_Worker");
            if (prefab == null)
            {
                Debug.LogWarning("Survivor_Worker model not found in Resources/Models/Characters.");
                return null;
            }

            GameObject residentHost = new GameObject("Survivor | " + name);
            if (parent != null)
            {
                residentHost.transform.SetParent(parent, true);
            }
            residentHost.transform.position = worldPosition;

            GameObject modelInstance = Instantiate(prefab, residentHost.transform, false);
            modelInstance.name = "Survivor_Worker_Root";

            SurvivorCharacterController controller = residentHost.AddComponent<SurvivorCharacterController>();
            controller.SetProfile(name, job);
            controller.SetSpawnPoint(worldPosition);
            return controller;
        }
    }
}
