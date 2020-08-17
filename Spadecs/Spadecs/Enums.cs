// This source file is part of Spadecs.
// Spadecs is available through the world-wide-web at this URL:
//   https://github.com/Conticop/Spadecs
//
// This source file is subject to the MIT license.
//
// Copyright (c) 2020
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

using System.Collections.Generic;
using System;

using c_ubyte = System.Byte;
using c_int32 = System.Int32;

namespace Spadecs
{
    public enum PyBool : c_ubyte
    {
        False = 0,
        True = 1,
        Pass = 2
    }

    public enum ETeam : c_int32
    {
        Blue = 0,
        Green = 1,
        Spectator = 2
    }

    public enum EWeapon : c_int32
    {
        Rifle,
        SMG,
        Shotgun
    }

    public enum EBodyPart : c_int32
    {
        Torso,
        Head,
        Arms,
        Legs,
        Melee
    }

    public enum ETool : c_int32
    {
        Spade,
        Block,
        Weapon,
        Grenade
    }

    public enum EBlockAction : c_int32
    {
        BuildBlock,
        DestroyBlock,
        SpadeDestroy,
        GrenadeDestroy
    }

    public enum EEntity : c_int32
    {
        BlueFlag,
        GreenFlag,
        BlueBase,
        GreenBase
    }

    public enum EChat : c_int32
    {
        All,
        Team,
        System
    }

    public enum EKillType : c_int32
    {
        Weapon,
        Headshot,
        Melee,
        Grenade,
        Fall,
        TeamChange,
        ClassChange
    }

    public enum EError : c_int32
    {
        Undefined,
        Banned,
        TooManyConnections,
        WrongVersion,
        Full,
        Shutdown,
        Kicked = 10,
        InvalidName = 20
    }

    public enum EGameMode : c_int32
    {
        CTF,
        TC
    }

    public interface IWeaponDamage
    {
        public int this[int index] { get; }

        public int Torso { get; }

        public int Head { get; }

        public int Arms { get; }

        public int Legs { get; }
    }

    public sealed class WeaponDamage : IWeaponDamage
    {
        public WeaponDamage(int torso, int head, int arms, int legs)
        {
            Torso = torso;
            Head = head;
            Arms = arms;
            Legs = legs;
        }

        public int this[int index] => index switch
        {
            (int)EBodyPart.Torso => Torso,
            (int)EBodyPart.Head => Head,
            (int)EBodyPart.Arms => Arms,
            (int)EBodyPart.Legs => Legs,
            _ => 0
        };

        public int Torso { get; }

        public int Head { get; }

        public int Arms { get; }

        public int Legs { get; }
    }

    public static class Constants
    {
        public const int
            MASTER_VERSION = 31,
            GAME_VERSION = 3
        ;

        public static readonly Dictionary<EWeapon, Type> Weapons = new()
        {
            [EWeapon.Rifle] = typeof(Rifle),
            [EWeapon.SMG] = typeof(SMG),
            [EWeapon.Shotgun] = typeof(Shotgun)
        };
    }
}