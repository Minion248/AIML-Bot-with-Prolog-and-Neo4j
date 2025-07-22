% family.pl - Enhanced Family Knowledge Base

% Basic facts about family relationships
father_of(john, simon).
father_of(john, mary).
father_of(robert, john).
father_of(david, alice).
father_of(simon, tom).
father_of(simon, lisa).
father_of(john, simon).
father_of(michael, john).

mother_of(susan, simon).
mother_of(susan, mary).
mother_of(linda, john).
mother_of(alice, tom).
mother_of(alice, lisa).
mother_of(mary, peter).

% Gender facts
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

% Derived rules
% Parent relationship (either father or mother)
parent_of(X, Y) :- father_of(X, Y).
parent_of(X, Y) :- mother_of(X, Y).

% Child relationship
child_of(X, Y) :- parent_of(Y, X).

% Son relationship
son_of(X, Y) :- parent_of(Y, X), male(X).

% Daughter relationship
daughter_of(X, Y) :- parent_of(Y, X), female(X).

% Sibling relationship
sibling_of(X, Y) :-
    parent_of(Z, X),
    parent_of(Z, Y),
    X \= Y.

% Brother relationship
brother_of(X, Y) :-
    sibling_of(X, Y),
    male(X).

% Sister relationship
sister_of(X, Y) :-
    sibling_of(X, Y),
    female(X).

% Grandparent relationship
grandparent_of(X, Z) :-
    parent_of(X, Y),
    parent_of(Y, Z).

% Grandfather relationship
grandfather_of(X, Z) :-
    grandparent_of(X, Z),
    male(X).

% Grandmother relationship
grandmother_of(X, Z) :-
    grandparent_of(X, Z),
    female(X).

% Grandchild relationship
grandchild_of(X, Y) :- grandparent_of(Y, X).

% Grandson relationship
grandson_of(X, Y) :-
    grandchild_of(X, Y),
    male(X).

% Granddaughter relationship
granddaughter_of(X, Y) :-
    grandchild_of(X, Y),
    female(X).

% Uncle relationship
uncle_of(X, Y) :-
    parent_of(Z, Y),
    brother_of(X, Z).

% Aunt relationship
aunt_of(X, Y) :-
    parent_of(Z, Y),
    sister_of(X, Z).

% Nephew relationship
nephew_of(X, Y) :-
    sibling_of(Y, Z),
    parent_of(Z, X),
    male(X).

% Niece relationship
niece_of(X, Y) :-
    sibling_of(Y, Z),
    parent_of(Z, X),
    female(X).

% Cousin relationship
cousin_of(X, Y) :-
    parent_of(A, X),
    parent_of(B, Y),
    sibling_of(A, B).

% Ancestor relationship
ancestor_of(X, Y) :- parent_of(X, Y).
ancestor_of(X, Y) :-
    parent_of(X, Z),
    ancestor_of(Z, Y).

% Descendant relationship
descendant_of(X, Y) :- ancestor_of(Y, X).

% Married couple (you can add more as needed)
married_to(john, susan).
married_to(susan, john).
married_to(david, alice).
married_to(alice, david).

% Spouse relationship
spouse_of(X, Y) :- married_to(X, Y).

% In-law relationships
father_in_law_of(X, Y) :-
    spouse_of(Y, Z),
    father_of(X, Z).

mother_in_law_of(X, Y) :-
    spouse_of(Y, Z),
    mother_of(X, Z).

% Utility predicates
% Check if someone is a parent
is_parent(X) :- parent_of(X, _).

% Check if someone has children
has_children(X) :- parent_of(X, _).

% Count children
count_children(X, Count) :-
    findall(Y, parent_of(X, Y), Children),
    length(Children, Count).

% Find all relatives of a person
relative_of(X, Y) :-
    ancestor_of(X, Y).
relative_of(X, Y) :-
    descendant_of(X, Y).
relative_of(X, Y) :-
    sibling_of(X, Y).
relative_of(X, Y) :-
    cousin_of(X, Y).
relative_of(X, Y) :-
    uncle_of(X, Y).
relative_of(X, Y) :-
    aunt_of(X, Y).
relative_of(X, Y) :-
    nephew_of(X, Y).
relative_of(X, Y) :-
    niece_of(X, Y).