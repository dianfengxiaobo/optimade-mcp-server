6   API Filtering Format Specification

An OPTIMADE filter expression is passed in the parameter filter as a URL query parameter as . The filter expression allows desired properties to be compared against search values; several such comparisons can be combined using the logical conjunctions AND, OR, NOT, and parentheses, with their usual semantics.

All properties marked as REQUIRED in section  MUST be queryable with all mandatory filter features. The level of query support REQUIRED for other properties is described in .

When provided as a URL query parameter, the contents of the filter parameter is URL-encoded by the client in the HTTP GET request, and then URL-decoded by the API implementation before any further parsing takes place. In particular, this means the client MUST escape special characters in string values as described below for  before the URL encoding, and the API implementation MUST first URL-decode the filter parameter before reversing the escaping of string tokens.

Examples of syntactically correct query strings embedded in queries:

http://example.org/optimade/v1/structures?filter=_exmpl_melting_point%3C300+AND+nelements=4+AND+chemical_formula_descriptive="SiO2"&response_format=xml

Or, fully URL encoded:

http://example.org/optimade/v1/structures?filter=_exmpl_melting_point%3C300+AND+nelements%3D4+AND+chemical_formula_descriptive%3D%22SiO2%22&response_format=xml

6.1   Lexical Tokens

The following tokens are used in the filter query component:

Property names: the first character MUST be a lowercase letter, the subsequent symbols MUST be composed of lowercase letters or digits; the underscore ("_", ASCII 95 dec (0x5F)) is considered to be a lower-case letter when defining identifiers. The length of the identifiers is not limited, except that when passed as a URL query parameter the whole query SHOULD NOT be longer than the limits imposed by the URI specification. This definition is similar to one used in most widespread programming languages, except that OPTIMADE limits allowed letter set to lowercase letters only. This allows to tell OPTIMADE identifiers and operator keywords apart unambiguously without consulting a reserved word table and to encode this distinction concisely in the EBNF Filter Language grammar.

Examples of valid property names:

band_gap

cell_length_a

cell_volume

Examples of incorrect property names:

0_kvak (starts with a number);

"foo bar" (contains space; contains quotes)

BadLuck (contains upper-case letters)

Identifiers that start with an underscore are specific to a database or definition provider, and MUST be on the format of a namespace prefix (see section ).

Examples:

_exmpl_formula_sum (a property specific to that database)

_exmpl_band_gap

_exmpl_supercell

_exmpl_trajectory

_exmpl_workflow_id

Nested property names A nested property name is composed of at least two identifiers separated by periods (.).

String values MUST be surrounded by double quote characters (", ASCII symbol 34 dec, 0x22 hex). A double quote that is a part of the value, not a delimiter, MUST be escaped by prepending it with a backslash character (\\, ASCII symbol 92 dec, 0x5C hex). A backslash character that is part of the value (i.e., not used to escape a double quote) MUST be escaped by prepending it with another backslash. An example of an escaped string value, including the enclosing double quotes, is given below:

"A double quote character (\", ASCII symbol 34 dec) MUST be prepended by a backslash (\\, ASCII symbol 92 dec) when it is a part of the value and not a delimiter; the backslash character \"\\\" itself MUST be preceded by another backslash, forming a double backslash: \\\\"

(Note that at the end of the string value above the four final backslashes represent the two terminal backslashes in the value, and the final double quote is a terminator, it is not escaped.)

String value tokens are also used to represent timestamps in form of the .

Numeric values are represented as decimal integers or in scientific notation, using the usual programming language conventions. A regular expression giving the number syntax is given below as a  or as a :

ERE: [-+]?([0-9]+(.[0-9]*)?|.[0-9]+)([eE][-+]?[0-9]+)?

PCRE: [-+]?(?:d+(.d*)?|.d+)(?:[eE][-+]?d+)?

An implementation of the search filter MAY reject numbers that are outside the machine representation of the underlying hardware; in such case it MUST return the error 501 Not Implemented with an appropriate error message that indicates the cause of the error and an acceptable number range.

Examples of valid numbers:

12345, +12, -34, 1.2, .2E7, -.2E+7, +10.01E-10, 6.03e23, .1E1, -.1e1, 1.e-12, -.1e-12, 1000000000.E1000000000, 1., .1

Examples of invalid numbers (although they MAY contain correct numbers as substrings):

1.234D12, .e1, -.E1, +.E2, 1.23E+++, +-123

Note: this number representation is more general than the number representation in JSON (for instance, 1. is a valid numeric value for the filtering language specified here, but is not a valid float number in JSON, where the correct format is 1.0 instead).

While the filtering language supports tests for equality between properties of floating point type and decimal numbers given in the filter string, such comparisons come with the usual caveats for testing for equality of floating point numbers. Normally, a client cannot rely on that a floating point number stored in a database takes on a representation that exactly matches the one obtained for a number given in the filtering string as a decimal number or as an integer. However, testing for equality to zero MUST be supported.

More examples of the number tokens and machine-readable definitions and tests can be found in the  (files integers.lst, , , and reals.lst).

Boolean values are represented with the tokens TRUE and FALSE.

Operator tokens are represented by usual mathematical relation symbols or by case-sensitive keywords. Currently the following operators are supported: =, !=, <=, >=, <, > for tests of number, string (lexicographical) or timestamp (temporal) equality, inequality, less-than, more-than, less, and more relations; AND, OR, NOT for logical conjunctions, and a number of keyword operators discussed in the next section.

In future extensions, operator tokens that are words MUST contain only upper-case letters. This requirement guarantees that no operator token will ever clash with a property name.

6.2   The Filter Language Syntax

All filtering expressions MUST follow the  grammar of appendix  of this specification. The appendix contains a complete machine-readable EBNF, including the definition of the lexical tokens described above in section . The EBNF is enclosed in special strings constructed as BEGIN and END, both followed by EBNF GRAMMAR Filter, to enable automatic extraction.

6.2.1   Basic boolean operations

The filter language supports conjunctions of comparisons using the boolean algebra operators "AND", "OR", and "NOT" and parentheses to group conjunctions. A comparison clause prefixed by NOT matches entries for which the comparison is false.

Examples:

NOT ( chemical_formula_hill = "Al" AND chemical_formula_anonymous = "A" OR chemical_formula_anonymous = "H2O" AND NOT chemical_formula_hill = "Ti" )

6.2.2   Numeric and String comparisons

Comparisons involving Numeric and String properties can be expressed using the usual comparison operators: '<', '>', '<=', '>=', '=', '!='. Implementations MUST support comparisons in the forms:

identifier <operator> constant

constant <operator> identifier

Where identifier is a property name and constant is either a numerical or string type constant.

Implementations MAY also support comparisons with identifiers on both sides, and comparisons with numerical type constants on both sides, i.e., in the forms:

identifier <operator> identifier

constant <operator> constant

However, the latter form, constant <operator> constant where the constants are strings MUST return the error 501 Not Implemented.

Note: The motivation to exclude the form constant <operator> constant for strings is that filter language strings can refer to data of different data types (e.g., strings and timestamps), and thus this construct is not unambiguous. The OPTIMADE specification will strive to address this issue in a future version.

Examples:

nelements > 3

chemical_formula_hill = "H2O" AND chemical_formula_anonymous != "AB"

_exmpl_aax <= +.1e8 OR nelements >= 10 AND NOT ( _exmpl_x != "Some string" OR NOT _exmpl_a = 7)

_exmpl_spacegroup="P2"

_exmpl_cell_volume<100.0

_exmpl_band_gap > 5.0 AND _exmpl_molecular_weight < 350

_exmpl_melting_point<300 AND nelements=4 AND chemical_formula_descriptive="SiO2"

_exmpl_some_string_property = 42 (This is syntactically allowed without putting 42 in quotation marks, see the notes about comparisons of values of different types below.)

5 < _exmpl_a

OPTIONAL: ((NOT (_exmpl_a>_exmpl_b)) AND _exmpl_x>0)

OPTIONAL: 5 < 7

6.2.3   Substring comparisons

In addition to the standard equality and inequality operators, matching of partial strings is provided by keyword operators:

identifier CONTAINS x: Is true if the substring value x is found anywhere within the property.

identifier STARTS WITH x: Is true if the property starts with the substring value x. The WITH keyword MAY be omitted.

identifier ENDS WITH x: Is true if the property ends with the substring value x. The WITH keyword MAY be omitted.

OPTIONAL features:

Support for x to be an identifier, rather than a string is OPTIONAL.

Examples:

chemical_formula_anonymous CONTAINS "C2" AND chemical_formula_anonymous STARTS WITH "A2"

chemical_formula_anonymous STARTS "A2" AND chemical_formula_anonymous ENDS WITH "D1"

6.2.4   Comparisons of boolean values

Straightforward comparisons ('=' and '!=') MUST be supported for boolean values. Other comparison operators ('<', '>', '<=', '>=') MUST NOT be supported. Boolean values are only supposed to be used in direct comparisons with properties, but not compound comparisons. For example, (nsites = 3 AND nelements = 3) = FALSE is not supported.

Boolean property property MAY be compared with TRUE by omitting the = TRUE altogether: property. Conversely, it MAY be compared with FALSE by negating the comparison with TRUE: NOT property.

Examples:

property = TRUE

property != FALSE

_exmpl_has_inversion_symmetry AND NOT _exmpl_is_primitive

6.2.5   Comparisons of list properties

In the following, list is a list-type property, and values is one or more value separated by commas (","), i.e., strings or numbers. An implementation MAY also support property names and nested property names in values.

The following constructs MUST be supported:

list HAS value: matches if at least one element in list is equal to value. (If list has no duplicate elements, this implements the set operator IN.)

list HAS ALL values: matches if, for each value, there is at least one element in list equal to that value. (If both list and values do not contain duplicate values, this implements the set operator >=.)

list HAS ANY values: matches if at least one element in list is equal to at least one value. (This is equivalent to a number of HAS statements separated by OR.)

list LENGTH value: matches if the number of items in the list property is equal to value.

The HAS ONLY construct MAY be supported:

OPTIONAL: list HAS ONLY values: matches if all elements in list are equal to at least one value. (If both list and values do not contain duplicate values, this implements the <= set operator.)

This construct is OPTIONAL as it can be difficult to realize in some underlying database implementations. However, if the desired search is over a property that can only take on a finite set of values (e.g., chemical elements) a client can formulate an equivalent search by inverting the list of values into inverse and express the filter as NOT list HAS inverse.

Furthermore, there is a set of OPTIONAL constructs that allows filters to be formulated over the values in correlated positions in multiple list properties. An implementation MAY support this syntax selectively only for specific properties. This type of filter is useful for, e.g., filtering on elements and correlated element counts available as two separate list properties.

list1:list2:... HAS val1:val2:...

list1:list2:... HAS ALL val1:val2:...

list1:list2:... HAS ANY val1:val2:...

list1:list2:... HAS ONLY val1:val2:...

Finally, all the above constructs that allow a value or lists of values on the right-hand side MAY allow <operator> value in each place a value can appear. In that case, a match requires that the <operator> comparison is fulfilled instead of equality. Strictly, the definitions of the HAS, HAS ALL, HAS ANY, HAS ONLY and LENGTH operators as written above apply, but with the word 'equal' replaced with the <operator> comparison.

For example:

OPTIONAL: list HAS < 3: matches all entries for which list contains at least one element that is less than three.

OPTIONAL: list HAS ALL < 3, > 3: matches only those entries for which list simultaneously contains at least one element less than three and one element greater than three.

An implementation MAY support combining the operator syntax with the syntax for correlated lists in particularly on a list correlated with itself. For example:

OPTIONAL: list:list HAS >=2:<=5: matches all entries for which list contains at least one element that is between the values 2 and 5.

Further examples of various comparisons of list properties:

OPTIONAL: elements HAS "H" AND elements HAS ALL "H","He","Ga","Ta" AND elements HAS ONLY "H","He","Ga","Ta" AND elements HAS ANY "H", "He", "Ga", "Ta"

OPTIONAL: elements HAS ONLY "H","He","Ga","Ta"

OPTIONAL: elements:_exmpl_element_counts HAS "H":6 AND elements:_exmpl_element_counts HAS ALL "H":6,"He":7 AND elements:_exmpl_element_counts HAS ONLY "H":6 AND elements:_exmpl_element_counts HAS ANY "H":6,"He":7 AND elements:_exmpl_element_counts HAS ONLY "H":6,"He":7

OPTIONAL: _exmpl_element_counts HAS < 3 AND _exmpl_element_counts HAS ANY > 3, = 6, 4, != 8 (note: specifying the = operator after HAS ANY is redundant here, if no operator is given, the test is for equality.)

OPTIONAL: elements:_exmpl_element_counts:_exmpl_element_weights HAS ANY > 3:"He":>55.3 , = 6:>"Ti":<37.6 , 8:<"Ga":0

6.2.6   Nested property names

Everywhere in a filter string where a property name is accepted, the API implementation MAY accept nested property names as described in section , consisting of identifiers separated by periods ('.'). A filter on a nested property name consisting of two identifiers identifier1.identifier2 matches if either one of these points are true:

identifier1 references a dictionary-type property that contains as an identifier identifier2 and the filter matches for the content of identifier2.

identifier1 references a list of dictionaries that contain as an identifier identifier2 and the filter matches for a flat list containing only the contents of identifier2 for every dictionary in the list. E.g., if identifier1 is the list [{"identifier2":42, "identifier3":36}, {"identifier2":96, "identifier3":66}], then identifier1.identifier2 is understood in the filter as the list [42, 96].

The API implementation MAY allow this notation to generalize to arbitrary depth. A nested property name that combines more than one list MUST, if accepted, be interpreted as a completely flattened list.

6.2.7   Filtering on relationships

As described in the section , it is possible for the API implementation to describe relationships between entries of the same, or different, entry types. The API implementation MAY support queries on relationships with an entry type <entry type> by using special nested property names:

<entry type>.id references a list of IDs of relationships with entries of the type <entry type>.

<entry type>.description references a correlated list of the human-readable descriptions of these relationships.

Hence, the filter language acts as, for every entry type, there is a property with that name which contains a list of dictionaries with two keys, id and description. For example: a client queries the structures endpoint with a filter that references calculations.id. For a specific structures entry, the nested property behaves as the list ["calc-id-43", "calc-id-96"] and would then, e.g., match the filter calculations.id HAS "calc-id-96". This means that the structures entry has a relationship with the calculations entry of that ID.

Note: formulating queries on relationships with entries that have specific property values is a multi-step process. For example, to find all structures with bibliographic references where one of the authors has the last name "Schmidt" is performed by the following two steps:

Query the references endpoint with a filter authors.lastname HAS "Schmidt" and store the id values of the returned entries.

Query the structures endpoint with a filter references.id HAS ANY <list-of-IDs>, where <list-of-IDs> are the IDs retrieved from the first query separated by commas.

(Note: the type of query discussed here corresponds to a "join"-type operation in a relational data model.)

6.2.8   Filtering on Properties with an unknown value

Properties can have an unknown value, see section .

Filters that match when the property is known, or unknown, respectively can be constructed using the following syntax:

identifier IS KNOWN

identifier IS UNKNOWN

Except for the above constructs, filters that use any form of comparison that involve properties of unknown values MUST NOT match. Hence, by definition, an identifier of value null never matches equality (=), inequality (<, <=, >, >=, !=) or other comparison operators besides identifier IS UNKNOWN and NOT identifier IS KNOWN. In particular, a filter that compares two properties that are both null for equality or inequality does not match.

Examples:

chemical_formula_hill IS KNOWN AND NOT chemical_formula_anonymous IS UNKNOWN

6.2.9   Precedence

The precedence (priority) of the operators MUST be as indicated in the list below:

Comparison and keyword operators (<, <=, =, HAS, STARTS, etc.) -- highest priority;

NOT

AND

OR -- lowest priority.

Examples:

NOT a > b OR c = 100 AND f = "C2 H6": this is interpreted as (NOT (a > b)) OR ( (c = 100) AND (f = "C2 H6") ) when fully braced.

a >= 0 AND NOT b < c OR c = 0: this is interpreted as ((a >= 0) AND (NOT (b < c))) OR (c = 0) when fully braced.

6.2.10   Type handling and conversions in comparisons

The definitions of specific properties in this standard define their types. Similarly, for , the database provider decides their types. In the syntactic constructs that can accommodate values of more than one type, types of all participating values are REQUIRED to match, with a single exception of timestamps (see below). Different types of values MUST be reported as 501 Not Implemented errors, meaning that type conversion is not implemented in the specification.

As the filter language syntax does not define a lexical token for timestamps, values of this type are expressed using string tokens in . In a comparison with a timestamp property, a string token represents a timestamp value that would result from parsing the string according to RFC 3339 Internet Date/Time Format. Interpretation failures MUST be reported with error 400 Bad Request.

6.2.11   Optional filter features

Some features of the filtering language are marked OPTIONAL. An implementation that encounters an OPTIONAL feature that it does not support MUST respond with error 501 Not Implemented with an explanation of which OPTIONAL construct the error refers to.

8.2   Structures Entries

structures entries (or objects) have the properties described above in section , as well as the following properties:

8.2.1   elements

Description: The chemical symbols of the different elements present in the structure.

Type: list of strings.

Requirements/Conventions:

Support: SHOULD be supported by all implementations, i.e., SHOULD NOT be null.

Query: MUST be a queryable property with support for all mandatory filter features.

The strings are the chemical symbols, i.e., either a single uppercase letter or an uppercase letter followed by a number of lowercase letters.

The order MUST be alphabetical.

MUST refer to the same elements in the same order, and therefore be of the same length, as elements_ratios, if the latter is provided.

Note: This property SHOULD NOT contain the string "X" to indicate non-chemical elements or "vacancy" to indicate vacancies (in contrast to the field chemical_symbols for the species property).

Examples:

["Si"]

["Al","O","Si"]

Query examples:

A filter that matches all records of structures that contain Si, Al and O, and possibly other elements: elements HAS ALL "Si", "Al", "O".

To match structures with exactly these three elements, use elements HAS ALL "Si", "Al", "O" AND elements LENGTH 3.

Note: length queries on this property can be equivalently formulated by filtering on the nelements property directly.

8.2.2   nelements

Description: Number of different elements in the structure as an integer.

Type: integer

Requirements/Conventions:

Support: SHOULD be supported by all implementations, i.e., SHOULD NOT be null.

Query: MUST be a queryable property with support for all mandatory filter features.

MUST be equal to the lengths of the list properties  and elements_ratios, if they are provided.

Examples:

3

Querying:

Note: queries on this property can equivalently be formulated using elements LENGTH.

A filter that matches structures that have exactly 4 elements: nelements=4.

A filter that matches structures that have between 2 and 7 elements: nelements>=2 AND nelements<=7.

8.2.3   elements_ratios

Description: Relative proportions of different elements in the structure.

Type: list of floats

Requirements/Conventions:

Support: SHOULD be supported by all implementations, i.e., SHOULD NOT be null.

Query: MUST be a queryable property with support for all mandatory filter features.

Composed by the proportions of elements in the structure as a list of floating point numbers.

The sum of the numbers MUST be 1.0 (within floating point accuracy)

MUST refer to the same elements in the same order, and therefore be of the same length, as , if the latter is provided.

Examples:

[1.0]

[0.3333333333333333, 0.2222222222222222, 0.4444444444444444]

Query examples:

Note: Useful filters can be formulated using the set operator syntax for correlated values. However, since the values are floating point values, the use of equality comparisons is generally inadvisable.

OPTIONAL: a filter that matches structures where approximately 1/3 of the atoms in the structure are the element Al is: elements:elements_ratios HAS ALL "Al":>0.3333, "Al":<0.3334.

8.2.4   chemical_formula_descriptive

Description: The chemical formula for a structure as a string in a form chosen by the API implementation.

Type: string

Requirements/Conventions:

Support: SHOULD be supported by all implementations, i.e., SHOULD NOT be null.

Query: MUST be a queryable property with support for all mandatory filter features.

The chemical formula is given as a string consisting of properly capitalized element symbols followed by integers or decimal numbers, balanced parentheses, square, and curly brackets (,), [,], {, }, commas, the +, -, : and = symbols. The parentheses are allowed to be followed by a number. Spaces are allowed anywhere except within chemical symbols. The order of elements and any groupings indicated by parentheses or brackets are chosen freely by the API implementation.

The string SHOULD be arithmetically consistent with the element ratios in the chemical_formula_reduced property.

It is RECOMMENDED, but not mandatory, that symbols, parentheses and brackets, if used, are used with the meanings prescribed by .

Examples:

"(H2O)2 Na"

"NaCl"

"CaCO3"

"CCaO3"

"(CH3)3N+ - [CH2]2-OH = Me3N+ - CH2 - CH2OH"

Query examples:

Note: the free-form nature of this property is likely to make queries on it across different databases inconsistent.

A filter that matches an exactly given formula: chemical_formula_descriptive="(H2O)2 Na".

A filter that does a partial match: chemical_formula_descriptive CONTAINS "H2O".

8.2.5   chemical_formula_reduced

Description: The reduced chemical formula for a structure as a string with element symbols and integer chemical proportion numbers. The proportion number MUST be omitted if it is 1.

Type: string

Requirements/Conventions:

Support: SHOULD be supported by all implementations, i.e., SHOULD NOT be null.

Query: MUST be a queryable property. However, support for filters using partial string matching with this property is OPTIONAL (i.e., BEGINS WITH, ENDS WITH, and CONTAINS). Intricate queries on formula components are instead suggested to be formulated using set-type filter operators on the multi valued elements and elements_ratios properties.

Element symbols MUST have proper capitalization (e.g., "Si", not "SI" for "silicon").

Elements MUST be placed in alphabetical order, followed by their integer chemical proportion number.

For structures with no partial occupation, the chemical proportion numbers are the smallest integers for which the chemical proportion is exactly correct.

For structures with partial occupation, the chemical proportion numbers are integers that within reasonable approximation indicate the correct chemical proportions. The precise details of how to perform the rounding is chosen by the API implementation.

No spaces or separators are allowed.

Examples:

"H2NaO"

"ClNa"

"CCaO3"

Query examples:

A filter that matches an exactly given formula is chemical_formula_reduced="H2NaO".

8.2.6   chemical_formula_hill

Description: The chemical formula for a structure in  with element symbols followed by integer chemical proportion numbers. The proportion number MUST be omitted if it is 1.

Type: string

Requirements/Conventions:

Support: OPTIONAL support in implementations, i.e., MAY be null.

Query: Support for queries on this property is OPTIONAL. If supported, only a subset of the filter features MAY be supported.

The overall scale factor of the chemical proportions is chosen such that the resulting values are integers that indicate the most chemically relevant unit of which the system is composed. For example, if the structure is a repeating unit cell with four hydrogens and four oxygens that represents two hydroperoxide molecules, chemical_formula_hill is "H2O2" (i.e., not "HO", nor "H4O4").

If the chemical insight needed to ascribe a Hill formula to the system is not present, the property MUST be handled as unset.

Element symbols MUST have proper capitalization (e.g., "Si", not "SI" for "silicon").

Elements MUST be placed in , followed by their integer chemical proportion number. Hill order means: if carbon is present, it is placed first, and if also present, hydrogen is placed second. After that, all other elements are ordered alphabetically. If carbon is not present, all elements are ordered alphabetically.

If the system has sites with partial occupation and the total occupations of each element do not all sum up to integers, then the Hill formula SHOULD be handled as unset.

No spaces or separators are allowed.

Examples:

"H2O2"

Query examples:

A filter that matches an exactly given formula is chemical_formula_hill="H2O2".

8.2.7   chemical_formula_anonymous

Description: The anonymous formula is the chemical_formula_reduced, but where the elements are instead first ordered by their chemical proportion number, and then, in order left to right, replaced by anonymous symbols A, B, C, ..., Z, Aa, Ba, ..., Za, Ab, Bb, ... and so on.

Type: string

Requirements/Conventions:

Support: SHOULD be supported by all implementations, i.e., SHOULD NOT be null.

Query: MUST be a queryable property. However, support for filters using partial string matching with this property is OPTIONAL (i.e., BEGINS WITH, ENDS WITH, and CONTAINS).

Examples:

"A2B"

"A42B42C16D12E10F9G5"

Querying:

A filter that matches an exactly given formula is chemical_formula_anonymous="A2B".

8.2.8   dimension_types

Description: List of three integers describing the periodicity of the boundaries of the unit cell. For each direction indicated by the three lattice_vectors, this list indicates if the direction is periodic (value 1) or non-periodic (value 0). Note: the elements in this list each refer to the direction of the corresponding entry in lattice_vectors and not the Cartesian x, y, z directions.

Type: list of integers.

Requirements/Conventions:

Support: SHOULD be supported by all implementations, i.e., SHOULD NOT be null.

Query: Support for queries on this property is OPTIONAL.

MUST be a list of length 3.

Each integer element MUST assume only the value 0 or 1.

Examples:

A nonperiodic structure, for example, for a single molecule: [0, 0, 0]

A unit cell that is periodic in the direction of the third lattice vector, for example for a carbon nanotube: [0, 0, 1]

For a 2D surface/slab, with a unit cell that is periodic in the direction of the first and third lattice vectors: [1, 0, 1]

For a bulk 3D system with a unit cell that is periodic in all directions: [1, 1, 1]

8.2.9   nperiodic_dimensions

Description: An integer specifying the number of periodic dimensions in the structure, equivalent to the number of non-zero entries in dimension_types.

Type: integer

Requirements/Conventions:

Support: SHOULD be supported by all implementations, i.e., SHOULD NOT be null.

Query: MUST be a queryable property with support for all mandatory filter features.

The integer value MUST be between 0 and 3 inclusive and MUST be equal to the sum of the items in the dimension_types property.

This property only reflects the treatment of the lattice vectors provided for the structure, and not any physical interpretation of the dimensionality of its contents.

Examples:

2 should be indicated in cases where dimension_types is any of [1, 1, 0], [1, 0, 1], [0, 1, 1].

Query examples:

Match only structures with exactly 3 periodic dimensions: nperiodic_dimensions=3

Match all structures with 2 or fewer periodic dimensions: nperiodic_dimensions<=2

8.2.10   lattice_vectors

Description: The three lattice vectors in Cartesian coordinates, in ångström (Å).

Type: list of list of floats or unknown values.

Requirements/Conventions:

Support: SHOULD be supported by all implementations, i.e., SHOULD NOT be null.

Query: Support for queries on this property is OPTIONAL. If supported, filters MAY support only a subset of comparison operators.

MUST be a list of three vectors a, b, and c, where each of the vectors MUST BE a list of the vector's coordinates along the x, y, and z Cartesian coordinates. (Therefore, the first index runs over the three lattice vectors and the second index runs over the x, y, z Cartesian coordinates).

For databases that do not define an absolute Cartesian system (e.g., only defining the length and angles between vectors), the first lattice vector SHOULD be set along x and the second on the xy-plane.

MUST always contain three vectors of three coordinates each, independently of the elements of property dimension_types. The vectors SHOULD by convention be chosen so the determinant of the lattice_vectors matrix is different from zero. The vectors in the non-periodic directions have no significance beyond fulfilling these requirements.

The coordinates of the lattice vectors of non-periodic dimensions (i.e., those dimensions for which dimension_types is 0) MAY be given as a list of all null values. If a lattice vector contains the value null, all coordinates of that lattice vector MUST be null.

Examples:

[[4.0,0.0,0.0],[0.0,4.0,0.0],[0.0,1.0,4.0]] represents a cell, where the first vector is (4, 0, 0), i.e., a vector aligned along the x axis of length 4 Å; the second vector is (0, 4, 0); and the third vector is (0, 1, 4).

8.2.11   space_group_symmetry_operations_xyz

Description: a list of symmetry operations given as general position x, y and z coordinates in algebraic form.

Type list of strings

Requirements/Conventions:

Support: OPTIONAL support in implementations, i.e., MAY be null.

The property is RECOMMENDED if coordinates are returned in a form to which these operations can or must be applied (e.g. fractional atom coordinates of an asymmetric unit).

The property is REQUIRED if symmetry operations are necessary to reconstruct the full model of the material and no other symmetry information (e.g., the Hall symbol) is provided that would allow the user to derive symmetry operations unambiguously.

Query: Support for queries on this property is not required and in fact is NOT RECOMMENDED.

MUST be null if nperiodic_dimensions is equal to 0.

Each symmetry operation is described by a string that gives that symmetry operation in Jones' faithful representation (Bradley & Cracknell, 1972: pp. 35-37), adapted for computer string notation.

The letters x, y and z that are typesetted with overbars in printed text represent coordinate values multiplied by -1 and are encoded as -x, -y and -z, respectively.

The syntax of the strings representing symmetry operations MUST conform to regular expressions given in appendix .

The interpretation of the strings MUST follow the conventions of the IUCr CIF core dictionary (IUCr, 2023). In particular, this property MUST explicitly provide all symmetry operations needed to generate all the atoms in the unit cell from the atoms in the asymmetric unit, for the setting used.

This symmetry operation set MUST always include the x,y,z identity operation.

The symmetry operations are to be applied to fractional atom coordinates. In case only Cartesian coordinates are available, these Cartesian coordinates must be converted to fractional coordinates before the application of the provided symmetry operations.

If the symmetry operation list is present, it MUST be compatible with other space group specifications (e.g. the ITC space group number, the Hall symbol, the Hermann-Mauguin symbol) if these are present.

Examples:

Space group operations for the space group with ITC number 3 (H-M symbol P 2, extended H-M symbol P 1 2 1, Hall symbol P 2y): ["x,y,z", "-x,y,-z"]

Space group operations for the space group with ITC number 5 (H-M symbol C 2, extended H-M symbol C 1 2 1, Hall symbol C 2y): ["x,y,z", "-x,y,-z", "x+1/2,y+1/2,z", "-x+1/2,y+1/2,-z"]

Notes: The list of space group symmetry operations applies to the whole periodic array of atoms and together with the lattice translations given in the lattice_vectors property provides the necessary information to reconstruct all atom site positions of the periodic material. Thus, the symmetry operations described in this property are only applicable to material models with at least one periodic dimension. This property is not meant to represent arbitrary symmetries of molecules, non-periodic (finite) collections of atoms or non-crystallographic symmetry.

Bibliographic References:

Bradley, C. J. and Cracknell, A. P. (1972) The Mathematical Theory of Symmetry in Solids. Oxford, Clarendon Press (paperback edition 2010) 745 p. ISBN .

IUCr (2023) Core dictionary (coreCIF) version 2.4.5; data name _space_group_symop_operation_xyz. Available from:  [Accessed 2023-06-18T16:46+03:00].

8.2.12   space_group_symbol_hall

Description: A Hall space group symbol representing the symmetry of the structure as defined in (Hall, 1981, 1981a).

Type: string

Requirements/Conventions:

Support: OPTIONAL support in implementations, i.e., MAY be null.

Query: Support for queries on this property is OPTIONAL.

The change-of-basis operations are used as defined in the International Tables of Crystallography (ITC) Vol. B, Sect. 1.4, Appendix A1.4.2 (IUCr, 2001).

Each component of the Hall symbol MUST be separated by a single space symbol.

If there exists a standard Hall symbol which represents the symmetry it SHOULD be used.

MUST be null if nperiodic_dimensions is not equal to 3.

Examples:

Space group symbols with explicit origin (the Hall symbols):

P 2c -2ac

-I 4bd 2ab 3

Space group symbols with change-of-basis operations:

P 2yb (-1/2*x+z,1/2*x,y)

-I 4 2 (1/2*x+1/2*y,-1/2*x+1/2*y,z)

Bibliographic References:

Hall, S. R. (1981) Space-group notation with an explicit origin. Acta Crystallographica Section A, 37, 517-525, International Union of Crystallography (IUCr), DOI: 

Hall, S. R. (1981a) Space-group notation with an explicit origin; erratum. Acta Crystallographica Section A, 37, 921-921, International Union of Crystallography (IUCr), DOI: 

IUCr (2001). International Tables for Crystallography vol. B. Reciprocal Space. Ed. U. Shmueli. 2-nd edition. Dordrecht/Boston/London, Kluwer Academic Publishers.



Description A human- and machine-readable string containing the short Hermann-Mauguin (H-M) symbol which specifies the space group of the structure in the response.

Type: string

Requirements/Conventions:

Support: OPTIONAL support in implementations, i.e., MAY be null.

Query: Support for queries on this property is OPTIONAL.

The H-M symbol SHOULD aim to convey the closest representation of the symmetry information that can be specified using the short format used in the International Tables for Crystallography vol. A (IUCr, 2005), Table 4.3.2.1 as described in the accompanying text.

The symbol MAY be a non-standard short H-M symbol.

The H-M symbol does not unambiguously communicate the axis, cell, and origin choice, and the given symbol SHOULD NOT be amended to convey this information.

To encode as character strings, the following adaptations MUST be made when representing H-M symbols given in their typesetted form:

the overbar above the numbers MUST be changed to the minus sign in front of the digit (e.g. '-2');

subscripts that denote screw axes are written as digits immediately after the axis designator without a space (e.g. 'P 32')

the space group generators MUST be separated by a single space (e.g. 'P 21 21 2');

there MUST be no spaces in the space group generator designation (i.e. use 'P 21/m', not the 'P 21 / m');

Examples:

C 2

P 21 21 21

Bibliographic References:

IUCr (2005). International Tables for Crystallography vol. A. Space-Group Symmetry. Ed. Theo Hahn. 5-th edition. Dordrecht, Springer.

8.2.14   space_group_symbol_hermann_mauguin_extended

Description A human- and machine-readable string containing the extended Hermann-Mauguin (H-M) symbol which specifies the space group of the structure in the response.

Type: string

Requirements/Conventions:

Support: OPTIONAL support in implementations, i.e., MAY be null.

Query: Support for queries on this property is OPTIONAL.

The H-M symbols SHOULD be given as specified in the International Tables for Crystallography vol. A (IUCr, 2005), Table 4.3.2.1.

The change-of-basis operation SHOULD be provided for the non-standard axis and cell choices.

The extended H-M symbol does not unambiguously communicate the origin choice, and the given symbol SHOULD NOT be amended to convey this information.

The description of the change-of-basis SHOULD follow conventions of the ITC Vol. B, Sect. 1.4, Appendix A1.4.2 (IUCr, 2001).

The same character string encoding conventions MUST be used as for the specification of the space_group_symbol_hermann_mauguin property.

Examples:

C 1 2 1

Bibliographic References:

IUCr (2001). International Tables for Crystallography vol. B. Reciprocal Space. Ed. U. Shmueli. 2-nd edition. Dordrecht/Boston/London, Kluwer Academic Publishers.

IUCr (2005). International Tables for Crystallography vol. A. Space-Group Symmetry. Ed. Theo Hahn. 5-th edition. Dordrecht, Springer.

8.2.15   space_group_it_number

Description: Space group number which specifies the space group of the structure as defined in the International Tables for Crystallography Vol. A. (IUCr, 2005).

Type: integer

Requirements/Conventions:

Support: OPTIONAL support in implementations, i.e., MAY be null.

Query: Support for queries on this property is OPTIONAL.

The integer value MUST be between 1 and 230.

MUST be null if nperiodic_dimensions is not equal to 3.

8.2.16   cartesian_site_positions

Description: Cartesian positions of each site in the structure. A site is usually used to describe positions of atoms; what atoms can be encountered at a given site is conveyed by the species_at_sites property, and the species themselves are described in the species property.

Type: list of list of floats

Requirements/Conventions:

Support: SHOULD be supported by all implementations, i.e., SHOULD NOT be null.

Query: Support for queries on this property is OPTIONAL. If supported, filters MAY support only a subset of comparison operators.

It MUST be a list of length equal to the number of sites in the structure, where every element is a list of the three Cartesian coordinates of a site expressed as float values in the unit angstrom (Å).

An entry MAY have multiple sites at the same Cartesian position (for a relevant use of this, see e.g., the property ).

Examples:

[[0,0,0],[0,0,2]] indicates a structure with two sites, one sitting at the origin and one along the (positive) z-axis, 2 Å away from the origin.

8.2.17   nsites

Description: An integer specifying the length of the cartesian_site_positions property.

Type: integer

Requirements/Conventions:

Support: SHOULD be supported by all implementations, i.e., SHOULD NOT be null.

Query: MUST be a queryable property with support for all mandatory filter features.

Examples:

42

Query examples:

Match only structures with exactly 4 sites: nsites=4

Match structures that have between 2 and 7 sites: nsites>=2 AND nsites<=7

8.2.18   species_at_sites

Description: Name of the species at each site (where values for sites are specified with the same order of the property cartesian_site_positions). The properties of the species are found in the property .

Type: list of strings.

Requirements/Conventions:

Support: SHOULD be supported by all implementations, i.e., SHOULD NOT be null.

Query: Support for queries on this property is OPTIONAL. If supported, filters MAY support only a subset of comparison operators.

MUST have length equal to the number of sites in the structure (first dimension of the list property cartesian_site_positions).

Each species name mentioned in the species_at_sites list MUST be described in the list property  (i.e. for each value in the species_at_sites list there MUST exist exactly one dictionary in the species list with the name attribute equal to the corresponding species_at_sites value).

Each site MUST be associated only to a single species. Note: However, species can represent mixtures of atoms, and multiple species MAY be defined for the same chemical element. This latter case is useful when different atoms of the same type need to be grouped or distinguished, for instance in simulation codes to assign different initial spin states.

Examples:

["Ti","O2"] indicates that the first site is hosting a species labeled "Ti" and the second a species labeled "O2".

["Ac", "Ac", "Ag", "Ir"] indicates that the first two sites contain the "Ac" species, while the third and fourth sites contain the "Ag" and "Ir" species, respectively.

8.2.19   species

Description: A list describing the species of the sites of this structure. Species can represent pure chemical elements, virtual-crystal atoms representing a statistical occupation of a given site by multiple chemical elements, and/or a location to which there are attached atoms, i.e., atoms whose precise location are unknown beyond that they are attached to that position (frequently used to indicate hydrogen atoms attached to another element, e.g., a carbon with three attached hydrogens might represent a methyl group, -CH3).

Type: list of dictionary with keys:

name: string (REQUIRED)

chemical_symbols: list of strings (REQUIRED)

concentration: list of float (REQUIRED)

attached: list of strings (OPTIONAL)

nattached: list of integers (OPTIONAL)

mass: list of floats (OPTIONAL)

original_name: string (OPTIONAL).

Requirements/Conventions:

Support: SHOULD be supported by all implementations, i.e., SHOULD NOT be null.

Query: Support for queries on this property is OPTIONAL. If supported, filters MAY support only a subset of comparison operators.

Each list member MUST be a dictionary with the following keys:

name: REQUIRED; gives the name of the species; the name value MUST be unique in the species list;

chemical_symbols: REQUIRED; MUST be a list of strings of all chemical elements composing this species. Each item of the list MUST be one of the following:

a valid chemical-element symbol, or

the special value "X" to represent a non-chemical element, or

the special value "vacancy" to represent that this site has a non-zero probability of having a vacancy (the respective probability is indicated in the concentration list, see below).

If any one entry in the species list has a chemical_symbols list that is longer than 1 element, the correct flag MUST be set in the list structure_features (see property structure_features).

concentration: REQUIRED; MUST be a list of floats, with same length as chemical_symbols. The numbers represent the relative concentration of the corresponding chemical symbol in this species. The numbers SHOULD sum to one. Cases in which the numbers do not sum to one typically fall only in the following two categories:

Numerical errors when representing float numbers in fixed precision, e.g. for two chemical symbols with concentrations 1/3 and 2/3, the concentration might look something like [0.33333333333, 0.66666666666]. If the client is aware that the sum is not one because of numerical precision, it can renormalize the values so that the sum is exactly one.

Experimental errors in the data present in the database. In this case, it is the responsibility of the client to decide how to process the data.

Note that concentrations are uncorrelated between different sites (even of the same species).

attached: OPTIONAL; if provided MUST be a list of length 1 or more of strings of chemical symbols for the elements attached to this site, or "X" for a non-chemical element.

nattached: OPTIONAL; if provided MUST be a list of length 1 or more of integers indicating the number of attached atoms of the kind specified in the value of the attached key.

The implementation MUST include either both or none of the attached and nattached keys, and if they are provided, they MUST be of the same length. Furthermore, if they are provided, the structure_features property MUST include the string site_attachments.

mass: OPTIONAL. If present MUST be a list of floats, with the same length as chemical_symbols, providing element masses expressed in a.m.u. Elements denoting vacancies MUST have masses equal to 0.

original_name: OPTIONAL. Can be any valid Unicode string, and SHOULD contain (if specified) the name of the species that is used internally in the source database.

Note: With regard to "source database", we refer to the immediate source being queried via the OPTIMADE API implementation. The main use of this field is for source databases that use species names, containing characters that are not allowed (see description of the list property species_at_sites).

For systems that have only species formed by a single chemical symbol, and that have at most one species per chemical symbol, SHOULD use the chemical symbol as species name (e.g., "Ti" for titanium, "O" for oxygen, etc.) However, note that this is OPTIONAL, and client implementations MUST NOT assume that the key corresponds to a chemical symbol, nor assume that if the species name is a valid chemical symbol, that it represents a species with that chemical symbol. This means that a species {"name": "C", "chemical_symbols": ["Ti"], "concentration": [1.0]} is valid and represents a titanium species (and not a carbon species).

It is NOT RECOMMENDED that a structure includes species that do not have at least one corresponding site.

Examples:

[ {"name": "Ti", "chemical_symbols": ["Ti"], "concentration": [1.0]} ]: any site with this species is occupied by a Ti atom.

[ {"name": "Ti", "chemical_symbols": ["Ti", "vacancy"], "concentration": [0.9, 0.1]} ]: any site with this species is occupied by a Ti atom with 90 % probability, and has a vacancy with 10 % probability.

[ {"name": "BaCa", "chemical_symbols": ["vacancy", "Ba", "Ca"], "concentration": [0.05, 0.45, 0.5], "mass": [0.0, 137.327, 40.078]} ]: any site with this species is occupied by a Ba atom with 45 % probability, a Ca atom with 50 % probability, and by a vacancy with 5 % probability.

[ {"name": "C12", "chemical_symbols": ["C"], "concentration": [1.0], "mass": [12.0]} ]: any site with this species is occupied by a carbon isotope with mass 12.

[ {"name": "C13", "chemical_symbols": ["C"], "concentration": [1.0], "mass": [13.0]} ]: any site with this species is occupied by a carbon isotope with mass 13.

[ {"name": "CH3", "chemical_symbols": ["C"], "concentration": [1.0], "attached": ["H"], "nattached": [3]} ]: any site with this species is occupied by a methyl group, -CH3, which is represented without specifying precise positions of the hydrogen atoms.

8.2.20   assemblies

Description: A description of groups of sites that are statistically correlated.

Type: list of dictionary with keys:

sites_in_groups: list of list of integers (REQUIRED)

group_probabilities: list of floats (REQUIRED)

Requirements/Conventions:

Support: OPTIONAL support in implementations, i.e., MAY be null.

Query: Support for queries on this property is OPTIONAL. If supported, filters MAY support only a subset of comparison operators.

The property SHOULD be null for entries that have no partial occupancies.

If present, the correct flag MUST be set in the list structure_features (see property structure_features).

Client implementations MUST check its presence (as its presence changes the interpretation of the structure).

If present, it MUST be a list of dictionaries, each of which represents an assembly and MUST have the following two keys:

sites_in_groups: Index of the sites (0-based) that belong to each group for each assembly.

Example: [[1], [2]]: two groups, one with the second site, one with the third. Example: [[1,2], [3]]: one group with the second and third site, one with the fourth.

group_probabilities: Statistical probability of each group. It MUST have the same length as sites_in_groups. It SHOULD sum to one. See below for examples of how to specify the probability of the occurrence of a vacancy. The possible reasons for the values not to sum to one are the same as already specified above for the concentration of each species, see property .

If a site is not present in any group, it means that it is present with 100 % probability (as if no assembly was specified).

A site MUST NOT appear in more than one group.

Examples (for each entry of the assemblies list):

{"sites_in_groups": [[0], [1]], "group_probabilities": [0.3, 0.7]}: the first site and the second site never occur at the same time in the unit cell. Statistically, 30 % of the times the first site is present, while 70 % of the times the second site is present.

{"sites_in_groups": [[1,2], [3]], "group_probabilities": [0.3, 0.7]}: the second and third sites are either present together or not present; they form the first group of atoms for this assembly. The second group is formed by the fourth site. Sites of the first group (the second and the third) are never present at the same time as the fourth site. 30 % of times sites 1 and 2 are present (and site 3 is absent); 70 % of times site 3 is present (and sites 1 and 2 are absent).

Notes:

Assemblies are essential to represent, for instance, the situation where an atom can statistically occupy two different positions (sites).

By defining groups, it is possible to represent, e.g., the case where a functional molecule (and not just one atom) is either present or absent (or the case where it is present in two conformations).

Considerations on virtual alloys and on vacancies: In the special case of a virtual alloy, these specifications allow two different, equivalent ways of specifying them. For instance, for a site at the origin with 30 % probability of being occupied by Si, 50 % probability of being occupied by Ge, and 20 % of being a vacancy, the following two representations are possible:

Using a single species:

{

  "cartesian_site_positions": [[0,0,0]],

  "species_at_sites": ["SiGe-vac"],

  "species": [

    {

      "name": "SiGe-vac",

      "chemical_symbols": ["Si", "Ge", "vacancy"],

      "concentration": [0.3, 0.5, 0.2]

    }

  ]

  // ...

}

Using multiple species and the assemblies:

{

  "cartesian_site_positions": [ [0,0,0], [0,0,0], [0,0,0] ],

  "species_at_sites": ["Si", "Ge", "vac"],

  "species": [

    { "name": "Si", "chemical_symbols": ["Si"], "concentration": [1.0] },

    { "name": "Ge", "chemical_symbols": ["Ge"], "concentration": [1.0] },

    { "name": "vac", "chemical_symbols": ["vacancy"], "concentration": [1.0] }

  ],

  "assemblies": [

    {

      "sites_in_groups": [ [0], [1], [2] ],

      "group_probabilities": [0.3, 0.5, 0.2]

    }

  ]

  // ...

}

It is up to the database provider to decide which representation to use, typically depending on the internal format in which the structure is stored. However, given a structure identified by a unique ID, the API implementation MUST always provide the same representation for it.

The probabilities of occurrence of different assemblies are uncorrelated. So, for instance in the following case with two assemblies:

{

  "assemblies": [

    {

      "sites_in_groups": [ [0], [1] ],

      "group_probabilities": [0.2, 0.8]

    },

    {

      "sites_in_groups": [ [2], [3] ],

      "group_probabilities": [0.3, 0.7]

    }

  ]

}

Site 0 is present with a probability of 20 % and site 1 with a probability of 80 %. These two sites are correlated (either site 0 or 1 is present). Similarly, site 2 is present with a probability of 30 % and site 3 with a probability of 70 %. These two sites are correlated (either site 2 or 3 is present). However, the presence or absence of sites 0 and 1 is not correlated with the presence or absence of sites 2 and 3 (in the specific example, the pair of sites (0, 2) can occur with 0.2*0.3 = 6 % probability; the pair (0, 3) with 0.2*0.7 = 14 % probability; the pair (1, 2) with 0.8*0.3 = 24 % probability; and the pair (1, 3) with 0.8*0.7 = 56 % probability).

8.2.21   structure_features

Description: A list of strings that flag which special features are used by the structure.

Type: list of strings

Requirements/Conventions:

Support: MUST be supported by all implementations, MUST NOT be null.

Query: MUST be a queryable property. Filters on the list MUST support all mandatory HAS-type queries. Filter operators for comparisons on the string components MUST support equality, support for other comparison operators are OPTIONAL.

MUST be an empty list if no special features are used.

MUST be sorted alphabetically.

If a special feature listed below is used, the list MUST contain the corresponding string.

If a special feature listed below is not used, the list MUST NOT contain the corresponding string.

List of strings used to indicate special structure features:

disorder: this flag MUST be present if any one entry in the  list has a chemical_symbols list that is longer than 1 element.

implicit_atoms: this flag MUST be present if the structure contains atoms that are not assigned to sites via the property species_at_sites (e.g., because their positions are unknown). When this flag is present, the properties related to the chemical formula will likely not match the type and count of atoms represented by the species_at_sites, , and  properties.

site_attachments: this flag MUST be present if any one entry in the  list includes attached and nattached.

assemblies: this flag MUST be present if the property  is present.

Examples:

A structure having implicit atoms and using assemblies: ["assemblies", "implicit_atoms"]

9   Appendices

9.1   The Filter Language EBNF Grammar

(* BEGIN EBNF GRAMMAR Filter *)

(* The top-level 'filter' rule: *)



Filter = [Spaces], Expression ;



(* Values *)



OrderedConstant = String | Number ;

UnorderedConstant = ( TRUE | FALSE ) ;



Value = ( UnorderedConstant | OrderedValue ) ;



OrderedValue = ( OrderedConstant | Property ) ;

(* Note: support for Property in OrderedValue is OPTIONAL *)



ValueListEntry = ( Value | ValueEqRhs | ValueRelCompRhs | FuzzyStringOpRhs ) ;

(* Note: support for ValueEqRhs, ValueRelCompRhs and FuzzyStringOpRhs in ValueListEntry are OPTIONAL *)



ValueList = ValueListEntry, { Comma, ValueListEntry } ;

ValueZip = ValueListEntry, Colon, ValueListEntry, { Colon, ValueListEntry } ;



ValueZipList = ValueZip, { Comma, ValueZip } ;



(* Expressions *)



Expression = ExpressionClause, [ OR, Expression ] ;



ExpressionClause = ExpressionPhrase, [ AND, ExpressionClause ] ;



ExpressionPhrase = [ NOT ], ( Comparison | OpeningBrace, Expression, ClosingBrace ) ;



Comparison = ConstantFirstComparison

           | PropertyFirstComparison ;

(* Note: support for ConstantFirstComparison is OPTIONAL *)



ConstantFirstComparison = ( OrderedConstant, ValueOpRhs

                          | UnorderedConstant, ValueEqRhs ) ;



PropertyFirstComparison = Property, [ ValueOpRhs

                                    | KnownOpRhs

                                    | FuzzyStringOpRhs

                                    | SetOpRhs

                                    | SetZipOpRhs

                                    | LengthOpRhs ] ;

(* Note: support for SetZipOpRhs in Comparison is OPTIONAL *)



ValueOpRhs = ( ValueEqRhs | ValueRelCompRhs ) ;



ValueEqRhs = EqualityOperator, Value ;



ValueRelCompRhs = RelativeComparisonOperator, OrderedValue ;



KnownOpRhs = IS, ( KNOWN | UNKNOWN ) ;



FuzzyStringOpRhs = CONTAINS, Value

                 | STARTS, [ WITH ], Value

                 | ENDS, [ WITH ], Value ;



SetOpRhs = HAS, ( ( Value | EqualityOperator, Value | RelativeComparisonOperator, OrderedValue | FuzzyStringOpRhs ) | ALL, ValueList | ANY, ValueList | ONLY, ValueList ) ;

(* Note: support for the alternatives with EqualityOperator, RelativeComparisonOperator, FuzzyStringOpRhs, and ONLY in SetOpRhs are OPTIONAL *)



SetZipOpRhs = PropertyZipAddon, HAS, ( ValueZip | ONLY, ValueZipList | ALL, ValueZipList | ANY, ValueZipList ) ;



PropertyZipAddon = Colon, Property, { Colon, Property } ;



LengthOpRhs = LENGTH, [ Operator ], Value ;

(* Note: support for [ Operator ] in LengthOpRhs is OPTIONAL *)



(* Property *)



Property = Identifier, { Dot, Identifier } ;



(* TOKENS *)



(* Separators: *)



OpeningBrace = '(', [Spaces] ;

ClosingBrace = ')', [Spaces] ;



Dot = '.', [Spaces] ;

Comma = ',', [Spaces] ;

Colon = ':', [Spaces] ;



(* Boolean relations: *)



AND = 'AND', [Spaces] ;

NOT = 'NOT', [Spaces] ;

OR = 'OR', [Spaces] ;



IS = 'IS', [Spaces] ;

KNOWN = 'KNOWN', [Spaces] ;

UNKNOWN = 'UNKNOWN', [Spaces] ;



CONTAINS = 'CONTAINS', [Spaces] ;

STARTS = 'STARTS', [Spaces] ;

ENDS = 'ENDS', [Spaces] ;

WITH = 'WITH', [Spaces] ;



LENGTH = 'LENGTH', [Spaces] ;

HAS = 'HAS', [Spaces] ;

ALL = 'ALL', [Spaces] ;

ONLY = 'ONLY', [Spaces] ;

ANY = 'ANY', [Spaces] ;



(* Comparison operator tokens: *)



Operator = ( EqualityOperator | RelativeComparisonOperator ) ;

EqualityOperator = [ '!' ], '=' , [Spaces] ;

RelativeComparisonOperator = ( '<' | '>' ), [ '=' ], [Spaces] ;



(* Boolean values *)



TRUE = 'TRUE', [Spaces] ;

FALSE = 'FALSE', [Spaces] ;



(* Property syntax *)



Identifier = LowercaseLetter, { LowercaseLetter | Digit }, [Spaces] ;



Letter = UppercaseLetter | LowercaseLetter ;



UppercaseLetter = 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H' | 'I'

                | 'J' | 'K' | 'L' | 'M' | 'N' | 'O' | 'P' | 'Q' | 'R'

                | 'S' | 'T' | 'U' | 'V' | 'W' | 'X' | 'Y' | 'Z' ;



LowercaseLetter = 'a' | 'b' | 'c' | 'd' | 'e' | 'f' | 'g' | 'h' | 'i'

                | 'j' | 'k' | 'l' | 'm' | 'n' | 'o' | 'p' | 'q' | 'r'

                | 's' | 't' | 'u' | 'v' | 'w' | 'x' | 'y' | 'z' | '_' ;



(* Strings: *)



String = '"', { EscapedChar }, '"', [Spaces] ;



EscapedChar = UnescapedChar | '\', '"' | '\', '\' ;



UnescapedChar = Letter | Digit | Space | Punctuator | UnicodeHighChar ;



Punctuator = '!' | '#' | '$' | '%' | '&' | "'" | '(' | ')' | '*' | '+'

           | ',' | '-' | '.' | '/' | ':' | ';' | '<' | '=' | '>' | '?'

           | '@' | '[' | ']' | '^' | '`' | '{' | '|' | '}' | '~' ;



(* BEGIN EBNF GRAMMAR Number *)

(* Number token syntax: *)



Number = [ Sign ] ,

         ( Digits, [ '.', [ Digits ] ] | '.' , Digits ),

         [ Exponent ], [Spaces] ;



Exponent =  ( 'e' | 'E' ) , [ Sign ] , Digits ;



Sign = '+' | '-' ;



Digits =  Digit, { Digit } ;



Digit = '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' ;



(* White-space: *)



(* Special character tokens: *)



tab = ? \t ?;

nl  = ? \n ?;

cr  = ? \r ?;

vt  = ? \v ?;

ff  = ? \f ?;



Space = ' ' | tab | nl | cr | vt | ff ;



Spaces = Space, { Space } ;



(* The 'UnicodeHighChar' specifies any Unicode character above 0x7F.

   It is specified in this grammar by an extension to EBNF that allows a

   regular expression to specify terminal symbol ranges. *)



UnicodeHighChar = ? [^\x00-\x7F] ? ;



(* END EBNF GRAMMAR Number *)

(* END EBNF GRAMMAR Filter *)

Note: when implementing a parser according this grammar, the implementers MAY choose to construct a lexer that ignores all whitespace (spaces, tabs, newlines, vertical tabulation and form feed characters, as described in the grammar 'Space' definition), and use such a lexer to recognize language elements that are described in the (* TOKENS *) section of the grammar. In that case, it can be beneficial to remove the '[Spaces]' element from the Filter = [Spaces], Expression definition as well and use the remaining grammar rules as a parser generator input (e.g., for yacc, bison, antlr).

9.2   Regular Expressions for OPTIMADE Filter Tokens

The string below contains Perl-Compatible Regular Expressions to recognize identifiers, number, and string values as specified in this specification.

#BEGIN PCRE identifiers

[a-z_][a-z_0-9]*

#END PCRE identifiers



#BEGIN PCRE numbers

[-+]?(?:\d+(\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?

#END PCRE numbers



#BEGIN PCRE strings

"([^\\"]|\\.)*"

#END PCRE strings

The strings below contain Extended Regular Expressions (EREs) to recognize identifiers, number, and string values as specified in this specification.

#BEGIN ERE identifiers

[a-z_][a-z_0-9]*

#END ERE identifiers



#BEGIN ERE numbers

[-+]?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][-+]?[0-9]+)?

#END ERE numbers



#BEGIN ERE strings

"([^\"]|\\.)*"

#END ERE strings

