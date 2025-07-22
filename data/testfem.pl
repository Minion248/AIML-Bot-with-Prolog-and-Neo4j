% family.pl - Clean and working Family Knowledge Base

% Facts: Father relationships
father_of(john, simon).
father_of(john, mary).
father_of(robert, john).
father_of(david, alice).
father_of(simon, tom).
father_of(simon, lisa).

% Facts: Mother relationships
mother_of(susan, simon).
mother_of(susan, mary).
mother_of(linda, john).
mother_of(alice, tom).
mother_of(alice, lisa).
mother_of(mary, peter).

% Facts: Gender
male(john).
male(simon).
male(robert).
male(david).
male(tom).
male(peter).

female(susan).
female(mary).
female(linda).
female(alice).
female(lisa).

% Rules: Parent
parent_of(X, Y) :- father_of(X, Y).
parent_of(X, Y) :- mother_of(X, Y).

% Rules: Child
child_of(X, Y) :- parent_of(Y, X).

% Rules: Son/Daughter
son_of(X, Y) :- parent_of(Y, X), male(X).
daughter_of(X, Y) :- parent_of(Y, X), female(X).

% Rules: Sibling
sibling_of(X, Y) :-
    parent_of(Z, X),
    parent_of(Z, Y),
    X \= Y.

% Rules: Brother/Sister
brother_of(X, Y) :- sibling_of(X, Y), male(X).
sister_of(X, Y) :- sibling_of(X, Y), female(X).

% Rules: Grandparent
grandparent_of(X, Z) :-
    parent_of(X, Y),
    parent_of(Y, Z).

grandfather_of(X, Z) :- grandparent_of(X, Z), male(X).
grandmother_of(X, Z) :- grandparent_of(X, Z), female(X).

% Rules: Grandchild
grandchild_of(X, Y) :- grandparent_of(Y, X).
grandson_of(X, Y) :- grandchild_of(X, Y), male(X).
granddaughter_of(X, Y) :- grandchild_of(X, Y), female(X).

% Rules: Uncle/Aunt
uncle_of(X, Y) :-
    parent_of(Z, Y),
    brother_of(X, Z).

aunt_of(X, Y) :-
    parent_of(Z, Y),
    sister_of(X, Z).

% Rules: Nephew/Niece
nephew_of(X, Y) :-
    sibling_of(Y, Z),
    parent_of(Z, X),
    male(X).

niece_of(X, Y) :-
    sibling_of(Y, Z),
    parent_of(Z, X),
    female(X).

% Rules: Cousin
cousin_of(X, Y) :-
    parent_of(A, X),
    parent_of(B, Y),
    sibling_of(A, B).

% Rules: Ancestor/Descendant
ancestor_of(X, Y) :- parent_of(X, Y).
ancestor_of(X, Y) :-
    parent_of(X, Z),
    ancestor_of(Z, Y).

descendant_of(X, Y) :- ancestor_of(Y, X).

% Rules: Marriage
married_to(john, susan).
married_to(susan, john).
married_to(david, alice).
married_to(alice, david).

spouse_of(X, Y) :- married_to(X, Y).

% Rules: In-laws
father_in_law_of(X, Y) :-
    spouse_of(Y, Z),
    father_of(X, Z).

mother_in_law_of(X, Y) :-
    spouse_of(Y, Z),
    mother_of(X, Z).

% Utility rules
is_parent(X) :- parent_of(X, _).
has_children(X) :- parent_of(X, _).

count_children(X, Count) :-
    findall(Y, parent_of(X, Y), Children),
    length(Children, Count).

relative_of(X, Y) :- ancestor_of(X, Y).
relative_of(X, Y) :- descendant_of(X, Y).
relative_of(X, Y) :- sibling_of(X, Y).
relative_of(X, Y) :- cousin_of(X, Y).
relative_of(X, Y) :- uncle_of(X, Y).
relative_of(X, Y) :- aunt_of(X, Y).
relative_of(X, Y) :- nephew_of(X, Y).
relative_of(X, Y) :- niece_of(X, Y).
