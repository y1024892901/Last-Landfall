using System;
using System.Collections.Generic;
using UnityEngine;
namespace LastLandfall.Prototype
{
 public static class VesselGridNavigation
 {
  static readonly Vector2Int[] Steps={Vector2Int.up,Vector2Int.right,Vector2Int.down,Vector2Int.left};
  public static bool Find(IslandConstructionGrid grid,Vector3 from,Vector3 to,bool water,out List<Vector3> points)
  {
   points=new List<Vector3>(); if(grid==null)return false;
   Vector2Int start=grid.PointToCell(grid.Root.InverseTransformPoint(from)), goal=grid.PointToCell(grid.Root.InverseTransformPoint(to));
   var prototype=UnityEngine.Object.FindAnyObjectByType<BuildPlacementPrototype>();
   bool Allowed(Vector2Int c){if(!grid.Contains(c))return water;var t=grid.GetTerrain(c);if(!water)return (t.AllowsRoad || c==goal && t.HasLand && t.MaximumSlope<=45f) && t.MinimumHeight>grid.SeaLevel+.02f && (c==start||c==goal||prototype==null||!prototype.IsNavigationCellOccupied(c));
    for(int x=-1;x<=1;x++)for(int z=-1;z<=1;z++){var n=c+new Vector2Int(x,z);if(!grid.Contains(n))continue;var h=grid.GetTerrain(n);if(h.HasLand&&h.MaximumHeight>grid.SeaLevel-.25f)return false;}return true;}
   if(!Allowed(goal))return false;
   var frontier=new SortedSet<(float,int,Vector2Int)>(Comparer<(float,int,Vector2Int)>.Create((a,b)=>{int order=a.Item1.CompareTo(b.Item1);return order!=0?order:a.Item2.CompareTo(b.Item2);}));var costs=new Dictionary<Vector2Int,float>();var previous=new Dictionary<Vector2Int,Vector2Int>();int serial=0;
   costs[start]=0;frontier.Add((0,serial++,start));int visits=0;
   while(frontier.Count>0&&visits++<100000){var item=frontier.Min;frontier.Remove(item);var c=item.Item3;if(c==goal){var route=new List<Vector2Int>();while(c!=start){route.Add(c);c=previous[c];}route.Reverse();foreach(var cell in route){var p=grid.CellCenter(cell);if(water)p.y=grid.SeaLevel;points.Add(grid.Root.TransformPoint(p));}if(points.Count==0)points.Add(to);return true;}
    foreach(var offset in Steps){var next=c+offset;if(!Allowed(next))continue;float cost=costs[c]+1;if(costs.TryGetValue(next,out float old)&&old<=cost)continue;costs[next]=cost;previous[next]=c;float h=Mathf.Abs(goal.x-next.x)+Mathf.Abs(goal.y-next.y);frontier.Add((cost+h,serial++,next));}}
   return false;
  }
 }
}
