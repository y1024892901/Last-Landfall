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
        [SerializeField] private float poseTransitionDuration = 0.28f;

        private struct BoneRestPose
        {
            public Transform transform;
            public Vector3 idlePosition;
            public Quaternion idleRotation;
        }

        private Vector3 spawnOrigin;
        private Vector3 currentTarget;
        private bool isWalking;
        private float nextStateTimer;
        private float stepCycle;
        private float walkBlend;
        private float idlePhaseOffset;
        private Transform leftLeg;
        private Transform rightLeg;
        private Transform leftArm;
        private Transform rightArm;
        private Transform neck;
        private Transform head;
        private Transform spine;
        private Transform spine1;
        private Quaternion leftLegRest, rightLegRest, leftArmRest, rightArmRest, headRest;
        private BoneRestPose[] boneRestPoses;
        private IslandConstructionGrid terrainGrid;
        private IslandGrassCover grassCover;
        private Animation importedAnimation;
        private string walkClip;
        private System.Collections.Generic.Queue<Vector3> commandRoute;
        private Action arrived;
        public bool IsRunning => commandRoute != null;
        public bool IsAboard { get; private set; }
        public void RunRoute(System.Collections.Generic.List<Vector3> route, Action done = null)
        { if (IsAboard || route == null || route.Count == 0) return; commandRoute = new System.Collections.Generic.Queue<Vector3>(route); arrived = done; }
        public void CancelOrder() { commandRoute = null; arrived = null; isWalking = false; }
        public void Board(Transform ship, int seat)
        { commandRoute = null; arrived = null; isWalking = false; IsAboard = true; transform.SetParent(ship, true); transform.localPosition = new Vector3(seat % 2 == 0 ? -.4f : .4f, .9f, -.4f + seat / 2 * .5f); }
        public void LeaveBoat(Vector3 point)
        { transform.SetParent(null, true); transform.position = point; spawnOrigin = point; IsAboard = false; }
        private void FollowCommand()
        {
            isWalking = true; Vector3 target = commandRoute.Peek(); Vector3 delta = Vector3.ProjectOnPlane(target - transform.position, Vector3.up);
            if (delta.sqrMagnitude > .001f) transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(delta), 12f * Time.deltaTime);
            transform.position = Vector3.MoveTowards(transform.position, target, walkSpeed * 2.1f * Time.deltaTime);
            if (Vector3.Distance(transform.position, target) < .03f) { commandRoute.Dequeue(); if (commandRoute.Count == 0) { commandRoute = null; isWalking = false; var callback = arrived; arrived = null; callback?.Invoke(); } }
        }

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
            idlePhaseOffset = UnityEngine.Random.Range(0f, Mathf.PI * 2f);

            // Imported FBX roots differ between Unity versions; find the actual
            // hip and shoulder pivots, with the whole limb parented beneath each.
            leftLeg = FindJoint("UpperLeg_Left", "LeftUpLeg");
            rightLeg = FindJoint("UpperLeg_Right", "RightUpLeg");
            leftArm = FindJoint("UpperArm_Left", "LeftArm");
            rightArm = FindJoint("UpperArm_Right", "RightArm");
            neck = FindJoint("Neck");
            head = FindJoint("Head");
            spine = FindJoint("Spine");
            spine1 = FindJoint("Spine1");

            importedAnimation = GetComponentInChildren<Animation>();
            if (importedAnimation != null)
            {
                importedAnimation.playAutomatically = false;
                foreach (AnimationState state in importedAnimation)
                {
                    if (walkClip == null || state.name.ToLowerInvariant().Contains("walk")) walkClip = state.name;
                    state.wrapMode = WrapMode.Loop;
                }
                importedAnimation.Stop();
                CaptureIdlePoseFromRig();
            }

            leftLegRest = leftLeg != null ? leftLeg.localRotation : Quaternion.identity;
            rightLegRest = rightLeg != null ? rightLeg.localRotation : Quaternion.identity;
            leftArmRest = leftArm != null ? leftArm.localRotation : Quaternion.identity;
            rightArmRest = rightArm != null ? rightArm.localRotation : Quaternion.identity;
            headRest = head != null ? head.localRotation : Quaternion.identity;
            var prototype = FindAnyObjectByType<BuildPlacementPrototype>();
            terrainGrid = prototype != null ? prototype.ConstructionGrid : null;
            grassCover = prototype != null ? prototype.GetComponent<IslandGrassCover>() : null;
        }

        private void CaptureIdlePoseFromRig()
        {
            Transform rigRoot = importedAnimation.transform;
            Transform[] allTransforms = rigRoot.GetComponentsInChildren<Transform>(true);
            int count = 0;
            for (int i = 0; i < allTransforms.Length; i++)
            {
                if (allTransforms[i] != rigRoot) count++;
            }

            boneRestPoses = new BoneRestPose[count];
            Vector3[] bindPos = new Vector3[count];
            Quaternion[] bindRot = new Quaternion[count];

            int idx = 0;
            for (int i = 0; i < allTransforms.Length; i++)
            {
                Transform t = allTransforms[i];
                if (t == rigRoot) continue;
                boneRestPoses[idx].transform = t;
                bindPos[idx] = t.localPosition;
                bindRot[idx] = t.localRotation;
                idx++;
            }

            // Sample 8 evenly spaced phases across the walk clip so we can relax
            // the A-pose arms into a natural standing arm posture (regardless of whether
            // the clip contains 1 or 2 walk cycles) while keeping planted bind-pose legs.
            AnimationState walkState = walkClip != null ? importedAnimation[walkClip] : null;
            if (walkState != null)
            {
                const int sampleCount = 8;
                Quaternion[] walkAvgRot = new Quaternion[count];

                walkState.enabled = true;
                walkState.weight = 1f;
                for (int s = 0; s < sampleCount; s++)
                {
                    walkState.normalizedTime = (float)s / sampleCount;
                    importedAnimation.Sample();
                    float sampleWeight = 1f / (s + 1);
                    for (int i = 0; i < count; i++)
                    {
                        Quaternion currentRot = boneRestPoses[i].transform.localRotation;
                        walkAvgRot[i] = s == 0 ? currentRot : Quaternion.Slerp(walkAvgRot[i], currentRot, sampleWeight);
                    }
                }

                walkState.enabled = false;
                walkState.weight = 0f;
                importedAnimation.Stop();

                for (int i = 0; i < count; i++)
                {
                    string boneName = boneRestPoses[i].transform.name;
                    boneRestPoses[i].idlePosition = bindPos[i];

                    bool isArmChain = boneName.IndexOf("Arm", StringComparison.OrdinalIgnoreCase) >= 0 ||
                                      boneName.IndexOf("Shoulder", StringComparison.OrdinalIgnoreCase) >= 0 ||
                                      boneName.IndexOf("Hand", StringComparison.OrdinalIgnoreCase) >= 0;
                    if (isArmChain)
                    {
                        boneRestPoses[i].idleRotation = Quaternion.Slerp(bindRot[i], walkAvgRot[i], 0.75f);
                    }
                    else
                    {
                        boneRestPoses[i].idleRotation = bindRot[i];
                    }

                    boneRestPoses[i].transform.localPosition = boneRestPoses[i].idlePosition;
                    boneRestPoses[i].transform.localRotation = boneRestPoses[i].idleRotation;
                }
            }
            else
            {
                for (int i = 0; i < count; i++)
                {
                    boneRestPoses[i].idlePosition = bindPos[i];
                    boneRestPoses[i].idleRotation = bindRot[i];
                }
            }
        }

        private Transform FindJoint(params string[] jointNames)
        {
            foreach (Transform child in GetComponentsInChildren<Transform>(true))
            {
                string childName = child.name;
                int colonIndex = childName.LastIndexOf(':');
                string strippedName = colonIndex >= 0 ? childName.Substring(colonIndex + 1) : childName;
                for (int i = 0; i < jointNames.Length; i++)
                {
                    if (string.Equals(childName, jointNames[i], StringComparison.Ordinal) ||
                        string.Equals(strippedName, jointNames[i], StringComparison.Ordinal))
                    {
                        return child;
                    }
                }
            }
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
            bool hasImportedWalk = importedAnimation != null && walkClip != null && boneRestPoses != null;

            if (IsAboard) isWalking = false;
            else if (commandRoute != null) FollowCommand();
            else if (isWalking)
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
                    }
                    else
                    {
                        transform.position = ground;

                        // Face move direction smoothly
                        Quaternion targetRot = Quaternion.LookRotation(moveDir, Vector3.up);
                        transform.rotation = Quaternion.Slerp(transform.rotation, targetRot, 8f * Time.deltaTime);
                    }
                }
                else
                {
                    isWalking = false;
                    nextStateTimer = UnityEngine.Random.Range(idleDurationMin, idleDurationMax);
                }
            }
            else
            {
                nextStateTimer -= Time.deltaTime;
                if (nextStateTimer <= 0f)
                {
                    PickNewDestination();
                }
            }

            float targetBlend = isWalking ? 1f : 0f;
            float duration = Mathf.Max(0.05f, poseTransitionDuration);
            walkBlend = Mathf.MoveTowards(walkBlend, targetBlend, Time.deltaTime / duration);

            if (hasImportedWalk)
            {
                if (walkBlend > 0.001f)
                {
                    // Reset baseline before Unity's internal Animation step so non-keyframed bones stay clean.
                    for (int i = 0; i < boneRestPoses.Length; i++)
                    {
                        Transform t = boneRestPoses[i].transform;
                        if (t == null) continue;
                        t.localPosition = boneRestPoses[i].idlePosition;
                        t.localRotation = boneRestPoses[i].idleRotation;
                    }

                    if (!importedAnimation.IsPlaying(walkClip))
                    {
                        importedAnimation.Play(walkClip);
                    }

                    AnimationState walkState = importedAnimation[walkClip];
                    if (walkState != null)
                    {
                        walkState.speed = isWalking
                            ? Mathf.Lerp(0.55f, IsRunning ? 1.8f : 1.0f, walkBlend)
                            : Mathf.Lerp(0.20f, 0.75f, walkBlend);
                    }
                }
                else if (importedAnimation.isPlaying)
                {
                    importedAnimation.Stop();
                }

                if (!IsAboard && commandRoute == null && !isWalking && TryGround(transform.position, out Vector3 idleGround))
                {
                    transform.position = new Vector3(transform.position.x, idleGround.y, transform.position.z);
                }
            }
            else
            {
                // Procedural fallback for legacy non-rigged models
                float smoothWalk = Mathf.SmoothStep(0f, 1f, walkBlend);
                if (walkBlend > 0.001f)
                {
                    stepCycle += Time.deltaTime * walkSpeed * 6.0f * smoothWalk;
                }

                float legSwing = Mathf.Sin(stepCycle) * (IsRunning ? 45f : 25f) * smoothWalk;
                float armSwing = -Mathf.Sin(stepCycle) * (IsRunning ? 38f : 22f) * smoothWalk;
                float verticalBob = Mathf.Abs(Mathf.Sin(stepCycle)) * 0.04f;
                float breath = Mathf.Sin(Time.time * 2.2f + idlePhaseOffset) * 0.015f;

                if (leftLeg != null) leftLeg.localRotation = leftLegRest * Quaternion.Euler(legSwing, 0f, 0f);
                if (rightLeg != null) rightLeg.localRotation = rightLegRest * Quaternion.Euler(-legSwing, 0f, 0f);
                if (leftArm != null) leftArm.localRotation = leftArmRest * Quaternion.Euler(armSwing, 0f, 0f);
                if (rightArm != null) rightArm.localRotation = rightArmRest * Quaternion.Euler(-armSwing, 0f, 0f);

                if (head != null)
                {
                    float headTurn = Mathf.Sin(Time.time * 0.8f + idlePhaseOffset) * 12f * (1f - smoothWalk);
                    head.localRotation = headRest * Quaternion.Euler(0f, headTurn, 0f);
                }

                Vector3 pos = transform.position;
                if (!IsAboard && commandRoute == null && TryGround(pos, out Vector3 ground))
                {
                    float verticalOffset = Mathf.Lerp(breath, verticalBob, smoothWalk);
                    transform.position = new Vector3(pos.x, ground.y + verticalOffset, pos.z);
                }
            }
        }

        private void LateUpdate()
        {
            if (importedAnimation == null || walkClip == null || boneRestPoses == null) return;

            float smoothWalk = Mathf.SmoothStep(0f, 1f, walkBlend);
            float t = Time.time + idlePhaseOffset;
            float breathPitch = Mathf.Sin(t * 2.2f) * 1.6f;
            float headYaw = Mathf.Sin(t * 0.75f) * 9.0f;
            float headPitch = Mathf.Sin(t * 1.25f + 0.8f) * 2.5f;

            for (int i = 0; i < boneRestPoses.Length; i++)
            {
                Transform bone = boneRestPoses[i].transform;
                if (bone == null) continue;

                Vector3 idlePos = boneRestPoses[i].idlePosition;
                Quaternion idleRot = boneRestPoses[i].idleRotation;

                if (bone == spine || bone == spine1)
                {
                    idleRot *= Quaternion.Euler(breathPitch, 0f, 0f);
                }
                else if (bone == head)
                {
                    idleRot *= Quaternion.Euler(headPitch, headYaw, 0f);
                }
                else if (bone == neck)
                {
                    idleRot *= Quaternion.Euler(headPitch * 0.4f, headYaw * 0.4f, 0f);
                }

                if (smoothWalk <= 0.0001f)
                {
                    bone.localPosition = idlePos;
                    bone.localRotation = idleRot;
                }
                else if (smoothWalk < 0.9999f)
                {
                    bone.localPosition = Vector3.Lerp(idlePos, bone.localPosition, smoothWalk);
                    bone.localRotation = Quaternion.Slerp(idleRot, bone.localRotation, smoothWalk);
                }
            }
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
            string tripoVariant = technician ? "Survival/Survival" : "Adventurer/Adventurer";
            GameObject prefab = Resources.Load<GameObject>("Models/Environment/Tripo/Characters/" + tripoVariant);
            if (prefab == null)
            {
                Debug.LogWarning("找不到 Tripo 幸存者模型：Resources/Models/Environment/Tripo/Characters/" + tripoVariant);
                return null;
            }

            GameObject residentHost = new GameObject("Survivor | " + name);
            if (parent != null)
            {
                residentHost.transform.SetParent(parent, true);
            }
            residentHost.transform.position = worldPosition;

            GameObject modelInstance = Instantiate(prefab, residentHost.transform, false);
            modelInstance.name = "Survivor_Tripo_Root";
            if (prefab.name == "Adventurer" || prefab.name == "Survival")
            {
                var renderers = modelInstance.GetComponentsInChildren<Renderer>();
                if (renderers.Length > 0)
                {
                    Bounds bounds = renderers[0].bounds;
                    foreach (var renderer in renderers) bounds.Encapsulate(renderer.bounds);
                    modelInstance.transform.localScale *= 1.75f / Mathf.Max(.001f, bounds.size.y);
                    bounds = renderers[0].bounds;
                    foreach (var renderer in renderers) bounds.Encapsulate(renderer.bounds);
                    modelInstance.transform.position += new Vector3(worldPosition.x - bounds.center.x,
                        worldPosition.y - bounds.min.y, worldPosition.z - bounds.center.z);
                }
                var texture = Resources.Load<Texture2D>("Models/Environment/Tripo/Characters/" + tripoVariant + "_BaseColor");
                var shader = Shader.Find("Universal Render Pipeline/Lit");
                if (shader != null && texture != null)
                {
                    var material = new Material(shader);
                    material.SetTexture("_BaseMap", texture);
                    material.SetFloat("_Smoothness", .15f);
                    foreach (var renderer in renderers)
                    {
                        var materials = new Material[renderer.sharedMaterials.Length];
                        for (int i = 0; i < materials.Length; i++) materials[i] = material;
                        renderer.sharedMaterials = materials;
                    }
                }
            }

            SurvivorCharacterController controller = residentHost.AddComponent<SurvivorCharacterController>();
            controller.SetProfile(name, job);
            controller.SetSpawnPoint(worldPosition);
            return controller;
        }
    }
}
