#ifndef DECOMP_H
#define DECOMP_H

#ifndef NDEBUG
// Disable size assertions for debug builds because the sizes differ between debug and release builds.
// Assert against the retail LEGO Racers 2 executable's release layouts.
#undef ENABLE_DECOMP_ASSERTS
#endif

#if defined(ENABLE_DECOMP_ASSERTS)
#define DECOMP_STATIC_ASSERT(V)                                                                                        \
	namespace                                                                                                          \
	{                                                                                                                  \
	typedef int foo[(V) ? 1 : -1];                                                                                     \
	}
#define DECOMP_SIZE_ASSERT(T, S) DECOMP_STATIC_ASSERT(sizeof(T) == S)
#else
#define DECOMP_STATIC_ASSERT(V)
#define DECOMP_SIZE_ASSERT(T, S)
#endif

#ifndef sizeOfArray
#define sizeOfArray(arr) (sizeof(arr) / sizeof(arr[0]))
#endif

typedef unsigned char undefined;
typedef unsigned short undefined2;
typedef unsigned int undefined4;

extern undefined4 g_foldingDummyVariable;

// Use STUB when a function has not yet been matched and/or is WIP.
#define STUB(val)                                                                                                      \
	do {                                                                                                               \
		g_foldingDummyVariable = val;                                                                                  \
	} while (0)

// Use MATCHING when a function is matched, but function folding inhibits success.
#define MATCHING(val)                                                                                                  \
	do {                                                                                                               \
		g_foldingDummyVariable = val;                                                                                  \
	} while (0)

// Call a dispatch-table slot with thiscall semantics: the object travels in ECX
// and EDX is left untouched, as in retail virtual calls. The project's tables
// hold __fastcall bridges (object, unused EDX, ...); passing NULL for EDX emits
// an "xor edx, edx" that retail does not have. Calling the same slot as a member
// function keeps the bridge ABI (ECX object, stack arguments, callee cleanup)
// and VC6 emits "call [reg + offset]". Argument and return types are taken from
// the slot. Usage: DecompThiscall(&m_vtable->m_slot, this, args...), or
// DecompThiscallVoid(...) for slots that return void.
struct DecompThiscallTarget {};
#define DECOMP_THISCALL_OBJECT(object) ((DecompThiscallTarget*) (object))

// VC6 cannot return a void expression, so void slots use DecompThiscallVoid.
// Parameter types come from the slot (A*); arguments (B*) convert to them.
template <class O>
inline void DecompThiscallVoid(void(__fastcall* const* p_slot)(O, void*), void* p_object)
{
	typedef void (DecompThiscallTarget::*Method)();
	(DECOMP_THISCALL_OBJECT(p_object)->*(*(const Method*) p_slot))();
}
template <class R, class O>
inline R DecompThiscall(R(__fastcall* const* p_slot)(O, void*), void* p_object)
{
	typedef R (DecompThiscallTarget::*Method)();
	return (DECOMP_THISCALL_OBJECT(p_object)->*(*(const Method*) p_slot))();
}
template <class O, class A1, class B1>
inline void DecompThiscallVoid(void(__fastcall* const* p_slot)(O, void*, A1), void* p_object, B1 p_a1)
{
	typedef void (DecompThiscallTarget::*Method)(A1);
	(DECOMP_THISCALL_OBJECT(p_object)->*(*(const Method*) p_slot))((A1) p_a1);
}
template <class R, class O, class A1, class B1>
inline R DecompThiscall(R(__fastcall* const* p_slot)(O, void*, A1), void* p_object, B1 p_a1)
{
	typedef R (DecompThiscallTarget::*Method)(A1);
	return (DECOMP_THISCALL_OBJECT(p_object)->*(*(const Method*) p_slot))((A1) p_a1);
}
template <class O, class A1, class A2, class B1, class B2>
inline void DecompThiscallVoid(void(__fastcall* const* p_slot)(O, void*, A1, A2), void* p_object, B1 p_a1, B2 p_a2)
{
	typedef void (DecompThiscallTarget::*Method)(A1, A2);
	(DECOMP_THISCALL_OBJECT(p_object)->*(*(const Method*) p_slot))((A1) p_a1, (A2) p_a2);
}
template <class R, class O, class A1, class A2, class B1, class B2>
inline R DecompThiscall(R(__fastcall* const* p_slot)(O, void*, A1, A2), void* p_object, B1 p_a1, B2 p_a2)
{
	typedef R (DecompThiscallTarget::*Method)(A1, A2);
	return (DECOMP_THISCALL_OBJECT(p_object)->*(*(const Method*) p_slot))((A1) p_a1, (A2) p_a2);
}
template <class O, class A1, class A2, class A3, class B1, class B2, class B3>
inline void DecompThiscallVoid(
	void(__fastcall* const* p_slot)(O, void*, A1, A2, A3),
	void* p_object,
	B1 p_a1,
	B2 p_a2,
	B3 p_a3
)
{
	typedef void (DecompThiscallTarget::*Method)(A1, A2, A3);
	(DECOMP_THISCALL_OBJECT(p_object)->*(*(const Method*) p_slot))((A1) p_a1, (A2) p_a2, (A3) p_a3);
}
template <class R, class O, class A1, class A2, class A3, class B1, class B2, class B3>
inline R DecompThiscall(R(__fastcall* const* p_slot)(O, void*, A1, A2, A3), void* p_object, B1 p_a1, B2 p_a2, B3 p_a3)
{
	typedef R (DecompThiscallTarget::*Method)(A1, A2, A3);
	return (DECOMP_THISCALL_OBJECT(p_object)->*(*(const Method*) p_slot))((A1) p_a1, (A2) p_a2, (A3) p_a3);
}

#endif // DECOMP_H
